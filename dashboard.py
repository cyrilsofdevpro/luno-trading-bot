"""
Flask dashboard for Luno trading bot.
Displays live price chart, trades, bot status, profit tracking, and strategy controls.
Run: python dashboard.py
Then open: http://localhost:5000
"""

import json
import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from smart_strategy import SmartStrategy
from profit_tracker import ProfitTracker
from notification_manager import NotificationManager
from dotenv import dotenv_values, load_dotenv
from luno_client import LunoClient
import subprocess
import psutil
import signal
import threading
import time
from backend.db.init_db import get_session
from backend.models.user import User


def get_request_credentials(require_user_keys=True):
    """Return (api_key, api_secret, user) for the current request.
    If require_user_keys is True and the logged-in user has no stored keys,
    return (None, None, user) so callers can return an instructive error.
    If no user is logged in, fall back to reading from .env (legacy behavior).
    """
    try:
        uid = session.get('user_id')
        if uid:
            s = get_session()
            u = s.query(User).filter_by(id=uid).first()
            if u:
                k = (u.luno_api_key or '').strip()
                sct = (u.luno_api_secret or '').strip()
                if k and sct:
                    return k, sct, u
                # user is logged in but has no keys
                # If this user is the configured default owner, allow falling
                # back to the global .env Luno keys so the owner can view/manage
                # the bot without re-saving keys into their profile.
                try:
                    # Use the same default owner fallback as ensure_default_owner so
                    # behavior is consistent whether or not the env var is set.
                    default_owner = (os.getenv('DEFAULT_OWNER_EMAIL') or 'ISRAELCHRISTOPHER406@GMAIL.COM').strip().lower()
                    if default_owner and (u.email or '').strip().lower() == default_owner:
                        cfg = dotenv_values('.env')
                        return cfg.get('LUNO_API_KEY'), cfg.get('LUNO_API_SECRET'), u
                except Exception:
                    pass

                if require_user_keys:
                    return None, None, u
                return None, None, u

        # No logged-in user (or fallback): use global .env credentials
        from dotenv import dotenv_values
        cfg = dotenv_values('.env')
        return cfg.get('LUNO_API_KEY'), cfg.get('LUNO_API_SECRET'), None
    except Exception:
        return None, None, None

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-dashboard-secret')
STATE_FILE = "bot_state.json"
TRADES_FILE = "trade_log.csv"
STATS_FILE = "profit_stats.json"
AUTO_SELL_STATE_FILE = "auto_sell_state.json"  # Track if monitor is running
LOG_FILE = os.getenv('BOT_LOG_FILE', 'bot.log')

# Minimum order sizes by pair (base asset volume). These are conservative defaults
# used to avoid attempting orders the exchange will reject. Adjust as needed.
MIN_ORDER_VOLUME = {
    'USDTNGN': 1.0,
    'USDCNGN': 1.0,
    'XBTNGN': 0.0001,
    'ETHNGN': 0.001,
    'SOLNGN': 0.01,
    'ATOMNGN': 0.1,
    'LTCNGN': 0.001,
    'XRPNGN': 1.0,
}

# Ensure log file exists so /api/logs won't 404 when bot hasn't run yet
try:
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
except Exception:
    pass

# Initialize strategy, tracker, and notification manager
strategy = SmartStrategy()
tracker = ProfitTracker()
notifier = NotificationManager()

# Ensure backend DB is initialized and create a default owner account if missing
def ensure_default_owner():
    try:
        s = get_session()
        default_email = os.getenv('DEFAULT_OWNER_EMAIL', 'ISRAELCHRISTOPHER406@GMAIL.COM')
        default_password = os.getenv('DEFAULT_OWNER_PASSWORD', 'ISRAEL123')
        # Normalize email to lowercase for storage and comparison
        default_email = (default_email or '').strip().lower()
        # Case-insensitive lookup: use ILIKE when available to avoid duplicate accounts
        try:
            user = s.query(User).filter(User.email.ilike(default_email)).first()
        except Exception:
            # Fallback to simple equality if ilike is not available in this environment
            user = s.query(User).filter_by(email=default_email).first()
        if not user:
            user = User(name='Bot Owner', email=default_email)
            user.set_password(default_password)
            # Optionally load default Luno keys from env if set
            default_luno_key = os.getenv('DEFAULT_LUNO_API_KEY')
            default_luno_secret = os.getenv('DEFAULT_LUNO_API_SECRET')
            if default_luno_key:
                user.luno_api_key = default_luno_key
            if default_luno_secret:
                user.luno_api_secret = default_luno_secret
            s.add(user)
            s.commit()
            print(f"Created default owner account: {default_email}")
        else:
            # Ensure the stored email is normalized to lowercase
            if user.email != default_email:
                user.email = default_email
                s.add(user)
                s.commit()
    except Exception as e:
        print(f"Failed to ensure default owner: {e}")

ensure_default_owner()


def start_auto_sell_on_startup():
    """Ensure the auto-sell monitor is running on server start.
    Reads AUTO_SELL_TARGET_PCT and PAIR from .env and starts auto_sell_monitor.py
    if it's not already running.
    """
    try:
        cfg = dotenv_values('.env')
        target_pct = float(cfg.get('AUTO_SELL_TARGET_PCT') or cfg.get('AUTO_SELL_TARGET_PCT', 2.0))
        pair = (cfg.get('PAIR') or cfg.get('TRADING_PAIR') or '').upper()

        status = get_auto_sell_status()
        pid = status.get('pid')
        running = status.get('running') and pid and is_process_alive(pid)

        if not running:
            print(f"Auto-sell monitor not running; starting monitor for pair={pair} target={target_pct}%")
            proc = subprocess.Popen([
                sys.executable, "auto_sell_monitor.py"
            ], cwd=os.path.dirname(os.path.abspath(__file__)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            set_auto_sell_status(True, proc.pid, target_pct)

            # Persist PAIR and AUTO_SELL_TARGET_PCT into .env so monitor sees them
            try:
                existing = dotenv_values('.env')
                existing['AUTO_SELL_TARGET_PCT'] = str(target_pct)
                if pair:
                    existing['PAIR'] = pair
                with open('.env', 'w') as f:
                    for k, v in existing.items():
                        f.write(f"{k}={v}\n")
            except Exception as e:
                print(f"Warning: could not persist .env values for auto-sell: {e}")
        else:
            print(f"Auto-sell monitor already running (PID: {pid})")
    except Exception as e:
        print(f"Failed to ensure auto-sell on startup: {e}")


# NOTE: start_auto_sell_on_startup() will be invoked after helper functions
# (get_auto_sell_status, set_auto_sell_status, is_process_alive) are defined.

# Global reference to auto-sell monitor process
_auto_sell_process = None
_auto_sell_lock = threading.Lock()


@app.before_request
def log_incoming_request():
    try:
        # Simple diagnostic logger to stdout so we can see incoming requests
        print(f"Incoming request: {request.method} {request.path} from {request.remote_addr}")
        try:
            sys.stdout.flush()
        except Exception:
            pass

        # Enforce authentication for most routes: users must be logged in to use the app.
        # Allow a small whitelist of public endpoints (login, signup, health, static files
        # and the TradingView webhook endpoints which are token-protected separately).
        public_prefixes = ['/static/', '/_static/']
        public_paths = [
            url_for('login'),
            url_for('signup'),
            url_for('healthz'),
            url_for('tradingview_webhook_status'),
            url_for('tradingview_webhook'),
        ]

        # Some environments may not have url_for available for endpoints if not yet bound;
        # fallback to path string checks.
        path = request.path or ''

        is_public = any(path.startswith(p) for p in public_prefixes) or path in public_paths

        if not is_public:
            # If user not logged in, deny access. For API requests return JSON 401,
            # for browser GETs redirect to login page so user can sign in/create account.
            uid = session.get('user_id')
            if not uid:
                # API endpoints - start with /api or requests with Accept: application/json
                wants_json = request.path.startswith('/api') or request.is_json or 'application/json' in (request.headers.get('Accept') or '')
                if wants_json or request.method != 'GET':
                    return jsonify({'success': False, 'error': 'Authentication required'}), 401
                else:
                    return redirect(url_for('login'))
    except Exception:
        pass


@app.route('/api/logs/debug')
def api_logs_debug():
    """Simple debug endpoint to verify /api/logs routing."""
    print("/api/logs/debug called")
    try:
        sys.stdout.flush()
    except Exception:
        pass
    return "OK: logs debug"


def read_state():
    """Read shared bot state and monitoring info."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Add monitoring fields for dashboard even if missing
    return {
        "last_price": 0,
        "pair": "XBTUSDC",
        "dry_run": False,
        "last_update": datetime.now().isoformat(),
        "prices": [],
        "balance": {},
        "bid": 0,
        "buy_price": 0,
        "spent_ngn": 0,
        "current_value_ngn": 0,
        "profit_ngn": 0,
        "profit_pct": 0,
        "auto_sell_target_pct": 0,
    }


def read_trades():
    """Parse CSV trade log."""
    import csv
    trades = []
    if os.path.exists(TRADES_FILE):
        try:
            with open(TRADES_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row and row.get('timestamp'):
                        trades.append({
                            "timestamp": row.get("timestamp", ""),
                            "pair": row.get("pair", ""),
                            "action": row.get("action", ""),
                            "price": row.get("price", "0"),
                            "volume": row.get("volume", "0"),
                            "details": row.get("details", ""),
                        })
        except Exception as e:
            print(f"Error reading trades: {e}")
    return trades[::-1]  # Reverse to show newest first


def append_trade_log_row(timestamp, pair, action, price, volume, details=None):
    """Append a trade row to the CSV trade log."""
    header = ['timestamp', 'pair', 'action', 'price', 'volume', 'details']
    exists = os.path.exists(TRADES_FILE)
    line = f"{timestamp},{pair},{action},{price},{volume},{json.dumps(details or {})}\n"
    # Ensure file exists and has header
    if not exists:
        with open(TRADES_FILE, 'w', encoding='utf-8') as f:
            f.write(','.join(header) + '\n')
    with open(TRADES_FILE, 'a', encoding='utf-8') as f:
        f.write(line)


def write_state(state: dict):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def update_tradingview_state(info: dict):
    """Merge tradingview info into the persistent state file."""
    try:
        st = read_state()
        st_tv = st.get('tradingview', {})
        st_tv.update(info)
        st['tradingview'] = st_tv
        write_state(st)
    except Exception:
        pass


def get_auto_sell_status():
    """Read auto-sell monitor status from state file."""
    if os.path.exists(AUTO_SELL_STATE_FILE):
        try:
            with open(AUTO_SELL_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'running': False, 'pid': None, 'target_pct': 2.0}


def set_auto_sell_status(running: bool, pid: int = None, target_pct: float = 2.0):
    """Write auto-sell monitor status to state file."""
    try:
        # Read existing status to preserve additional fields such as held_pairs
        existing = {}
        if os.path.exists(AUTO_SELL_STATE_FILE):
            try:
                with open(AUTO_SELL_STATE_FILE, 'r', encoding='utf-8') as f:
                    existing = json.load(f) or {}
            except Exception:
                existing = {}

        existing.update({'running': running, 'pid': pid, 'target_pct': target_pct})
        with open(AUTO_SELL_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f)
    except Exception:
        pass


def is_process_alive(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    try:
        return psutil.pid_exists(pid)
    except:
        return False


def get_min_volume_for_pair(pair: str) -> float:
    """Return a conservative minimum volume for the given trading pair's base asset.
    Falls back to a very small value if unknown.
    """
    try:
        p = (pair or '').upper()
        if p in MIN_ORDER_VOLUME:
            return float(MIN_ORDER_VOLUME[p])
        # Try to map by suffix (quote) detection, e.g., USDTNGN -> USDTNGN
        for k in MIN_ORDER_VOLUME.keys():
            if p.endswith(k[-3:]):
                return float(MIN_ORDER_VOLUME[k])
    except Exception:
        pass
    return 0.000001


def get_held_pairs():
    """Return a list of currently held pairs from the auto-sell state file."""
    try:
        status = get_auto_sell_status()
        return status.get('held_pairs', []) or []
    except Exception:
        return []


def set_hold_for_pair(pair: str, hold: bool):
    """Add or remove a pair from the held_pairs list in the auto-sell state file."""
    try:
        status = get_auto_sell_status()
        held = set([p.upper() for p in (status.get('held_pairs') or [])])
        pair_u = (pair or '').upper()
        if hold:
            held.add(pair_u)
        else:
            held.discard(pair_u)
        status['held_pairs'] = sorted(list(held))
        # Persist full status dict back to file
        try:
            with open(AUTO_SELL_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(status, f)
        except Exception:
            pass
        return True
    except Exception:
        return False


# Start the auto-sell monitor now that helper functions are defined
try:
    start_auto_sell_on_startup()
except Exception as _e:
    print(f"Auto-sell startup invocation failed: {_e}")



@app.route("/")
def index():
    """Serve dashboard HTML."""
    user_info = None
    try:
        uid = session.get('user_id')
        if uid:
            s = get_session()
            u = s.query(User).filter_by(id=uid).first()
            if u:
                user_info = {'id': u.id, 'name': u.name, 'email': u.email}
    except Exception:
        user_info = None
    return render_template("index.html", user=user_info)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    data = request.form or request.get_json() or {}
    name = data.get('name')
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    if not all([name, email, password]):
        flash('please provide name, email and password')
        return render_template('signup.html'), 400
    s = get_session()
    if s.query(User).filter_by(email=email).first():
        flash('email already registered')
        return render_template('signup.html'), 409
    user = User(name=name, email=email)
    user.set_password(password)
    s.add(user)
    s.commit()
    # log in
    session['user_id'] = user.id
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.form or request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    s = get_session()
    # Allow case-insensitive lookup
    try:
        user = s.query(User).filter(User.email.ilike(email)).first()
    except Exception:
        user = s.query(User).filter_by(email=email).first()

    if not user or not user.check_password(password):
        flash('invalid credentials')
        return render_template('login.html'), 401
    session['user_id'] = user.id
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route("/api/status")
def api_status():
    """Get bot status, latest price, and monitoring info."""
    # Return a limited view when the logged-in user hasn't provided their own Luno keys.
    try:
        api_key, api_secret, user = get_request_credentials(require_user_keys=False)
        state = read_state()

        # If a user is logged in but hasn't added keys, don't expose the global owner bot state.
        if user and (not api_key or not api_secret):
            return jsonify({
                "status": "limited",
                "message": "enter your luno account api & secret in Credentials to have full access",
                "needs_keys": True,
                "pair": state.get("pair", "--"),
                "last_price": None,
                "dry_run": state.get("dry_run", False),
                "last_update": None,
                "balance": {},
                "bid": None,
                "buy_price": None,
                "spent_ngn": None,
                "current_value_ngn": None,
                "profit_ngn": None,
                "profit_pct": None,
                "auto_sell_target_pct": state.get("auto_sell_target_pct", 0),
                "active_coin": strategy.get_active_coin(),
            })

        # Otherwise return the full state (owner/global or users with keys)
        return jsonify({
            "status": "running",
            "pair": state.get("pair", "XBTUSDC"),
            "last_price": state.get("last_price", 0),
            "dry_run": state.get("dry_run", False),
            "last_update": state.get("last_update"),
            "balance": state.get("balance", {}),
            # Monitoring info
            "bid": state.get("bid", 0),
            "buy_price": state.get("buy_price", 0),
            "spent_ngn": state.get("spent_ngn", 0),
            "current_value_ngn": state.get("current_value_ngn", 0),
            "profit_ngn": state.get("profit_ngn", 0),
            "profit_pct": state.get("profit_pct", 0),
            "auto_sell_target_pct": state.get("auto_sell_target_pct", 0),
            "active_coin": strategy.get_active_coin(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route("/api/strategy")
def api_strategy():
    """Get strategy configuration and stats."""
    active_coin = strategy.get_active_coin()
    coin_cfg = strategy.get_coin_config(active_coin)
    
    # Compute profit stats
    tracker.save_stats(STATS_FILE)
    stats = {}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
        except:
            pass
    
    return jsonify({
        'active_coin': active_coin,
        'supported_coins': strategy.list_coins(),
        'config': coin_cfg,
        'stats': stats,
    })


@app.route("/api/strategy/coin", methods=['POST'])
def api_set_coin():
    """Switch active trading coin."""
    data = request.get_json()
    coin = data.get('coin')
    try:
        strategy.set_active_coin(coin)
        return jsonify({'success': True, 'active_coin': coin})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/api/strategy/config", methods=['GET', 'POST'])
def api_update_config():
    """Update strategy config for active coin (POST) or return current config (GET)."""
    try:
        if request.method == 'GET':
            # Allow clients to fetch the current config via GET
            coin = request.args.get('coin') or strategy.get_active_coin()
            return jsonify({'success': True, 'config': strategy.get_coin_config(coin)})

        # POST: update config
        data = request.get_json() or {}
        coin = data.get('coin') or strategy.get_active_coin()

        # Extract known config keys
        cfg_update = {}
        for key in ['buy_drop_pct', 'sell_profit_pct', 'stop_loss_pct', 'compound_reinvest_pct', 'enabled']:
            if key in data:
                cfg_update[key] = data[key]

        strategy.update_coin_config(coin, **cfg_update)
        return jsonify({'success': True, 'config': strategy.get_coin_config(coin)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/api/prices")
def api_prices():
    """Get price history."""
    state = read_state()
    prices = state.get("prices", [])
    # Keep last 100 prices
    return jsonify({"prices": prices[-100:]})


@app.route('/api/ticker')
def api_ticker():
    """Fetch current ticker for an arbitrary pair (public Luno API).
    Query param: pair (e.g. USDTNGN)
    Returns: { success: True, pair: pair, price: float }
    """
    pair = request.args.get('pair') or request.args.get('symbol') or 'USDTNGN'
    try:
        # Use LunoClient to fetch public ticker data
        load_dotenv()
        cfg = dotenv_values('.env')
        client = LunoClient(cfg.get('LUNO_API_KEY'), cfg.get('LUNO_API_SECRET'))
        ticker = client.get_ticker(pair)
        # Determine a sensible price (ask preferred, then last, then bid)
        price_val = float(ticker.get('ask') or ticker.get('last') or ticker.get('bid') or 0)
        return jsonify({'success': True, 'pair': pair, 'price': price_val, **ticker})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/api/trades")
def api_trades():
    """Get recent trades."""
    trades = read_trades()
    return jsonify({"success": True, "trades": trades[:50]})  # Last 50 trades


@app.route('/api/logs')
def api_logs():
    """Return the last N lines from the bot log file for the dashboard terminal view.
    Query params: lines (int, default 200)
    """
    lines = int(request.args.get('lines') or 200)
    log_file = os.getenv('BOT_LOG_FILE', 'bot.log')
    output = []
    if os.path.exists(log_file):
        try:
            # Read last N lines efficiently
            with open(log_file, 'rb') as f:
                f.seek(0, os.SEEK_END)
                filesize = f.tell()
                block_size = 1024
                blocks = []
                remaining = filesize
                while remaining > 0 and len(b''.join(blocks).splitlines()) <= lines:
                    read_size = min(block_size, remaining)
                    f.seek(remaining - read_size)
                    blocks.insert(0, f.read(read_size))
                    remaining -= read_size
                data = b''.join(blocks).splitlines()[-lines:]
                output = [line.decode('utf-8', errors='replace') for line in data]
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': True, 'lines': len(output), 'logs': output})


@app.route('/api/logs/status')
def api_logs_status():
    """Return availability status for logs endpoint and whether log file exists."""
    log_file = os.getenv('BOT_LOG_FILE', 'bot.log')
    exists = os.path.exists(log_file)
    return jsonify({'success': True, 'available': True, 'log_file': log_file, 'exists': exists})


@app.route("/api/alerts/status")
def api_alerts_status():
    """Get alert channel status."""
    return jsonify({
        'channels': notifier.get_channels_status(),
        'enabled_channels': notifier.get_enabled_channels(),
    })


@app.route("/api/alerts/test", methods=['POST'])
def api_alerts_test():
    """Send test alert to all enabled channels."""
    try:
        notifier.send_trade_alert(
            action='TEST',
            pair='USDTNGN',
            price=1476.88,
            volume=0.01,
            order_id='TEST-ORDER-123',
        )
        return jsonify({'success': True, 'message': 'Test alert sent to all enabled channels'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/api/alerts/trade", methods=['POST'])
def api_alerts_trade():
    """Send trade execution alert."""
    try:
        data = request.json
        notifier.send_trade_alert(
            action=data.get('action', 'BUY'),
            pair=data.get('pair', 'USDTNGN'),
            price=float(data.get('price', 0)),
            volume=float(data.get('volume', 0)),
            order_id=data.get('order_id'),
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/api/alerts/summary", methods=['POST'])
def api_alerts_summary():
    """Send daily summary alert."""
    try:
        stats = tracker.compute_total_stats()
        notifier.send_daily_summary(stats)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/trade/place', methods=['POST'])
def api_trade_place():
    """Place a manual trade via the dashboard. Payload: pair, side, volume, price (optional), order_type ('limit'|'market')."""
    try:
        data = request.get_json() or {}
        pair = data.get('pair') or os.getenv('PAIR') or 'USDTNGN'
        side = (data.get('side') or 'buy').lower()
        volume = float(data.get('volume', 0))
        order_type = (data.get('order_type') or 'limit').lower()
        price = data.get('price')

        if side not in ('buy', 'sell'):
            return jsonify({'success': False, 'error': 'side must be buy or sell'}), 400
        if volume <= 0:
            return jsonify({'success': False, 'error': 'volume must be > 0'}), 400

        # Use per-user credentials where possible. Users must provide their own keys
        # to use trading features.
        api_key, api_secret, user = get_request_credentials(require_user_keys=True)
        if user and (not api_key or not api_secret):
            return jsonify({'success': False, 'error': 'no_user_keys', 'message': 'enter your luno account api & secret in Credentials to have full access.'}), 400

        # Allow override from request for safe testing: payload { dry_run: true }
        cfg = dotenv_values('.env')
        if 'dry_run' in data:
            dry = bool(data.get('dry_run'))
        else:
            dry = cfg.get('DRY_RUN', 'true').lower() == 'true'

        client = LunoClient(api_key, api_secret, dry_run=dry)

        # If market order requested, use current ticker to set a reasonable price (best bid/ask)
        if order_type == 'market' or not price:
            ticker = client.get_ticker(pair)
            # For buy use ask, for sell use bid; fallback to last
            if side == 'buy':
                price_val = float(ticker.get('ask') or ticker.get('last') or 0)
            else:
                price_val = float(ticker.get('bid') or ticker.get('last') or 0)
        else:
            price_val = float(price)

        # Minimum-order-size check to prevent exchange rejections
        min_vol = get_min_volume_for_pair(pair)
        if volume < min_vol:
            base_asset = pair.replace('NGN', '').replace('USD', '').replace('USDT', '').replace('USDC', '')
            error_msg = f'❌ Volume too small: You have {volume} {base_asset} but need at least {min_vol} {base_asset} to trade {pair}. Please increase your amount.'
            try:
                with open('trade_errors.log', 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().isoformat()}] VOLUME_TOO_SMALL: pair={pair}, available={volume}, minimum={min_vol}\n")
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'volume_too_small', 'message': error_msg}), 400

        # Place order. Use the order_type requested by the caller (limit|market).
        # If caller asked for a market order we still send a price (current ticker) to
        # avoid API variants that reject empty price fields. The LunoClient will
        # respect dry_run and raise helpful errors on failure.
        try:
            resp = client.place_order(pair, side, volume, price_val, order_type=order_type)
        except Exception as e:
            # Try to return a helpful error message to the client instead of a generic
            # "one or more arguments are invalid" message from the UI.
            err_msg = str(e)
            return jsonify({'success': False, 'error': 'order_failed', 'message': err_msg}), 400

        # Log the trade
        ts = datetime.now().timestamp()
        append_trade_log_row(ts, pair, side.upper(), price_val, volume, details={'order_resp': resp})

        # Update state summary
        state = read_state()
        state.update({
            'pair': pair,
            'last_price': price_val,
            'last_update': datetime.now().isoformat(),
        })
        # If this was a buy, update buy_price/volume; if sell, clear buy_price
        if side == 'buy':
            state['buy_price'] = price_val
            state['volume'] = volume
        else:
            state['buy_price'] = 0
            state['volume'] = 0

        write_state(state)

        # Notify channels about trade
        try:
            notifier.send_trade_alert(action=side.upper(), pair=pair, price=price_val, volume=volume, order_id=resp.get('order_id') or resp.get('id'))
        except Exception:
            pass

        return jsonify({'success': True, 'order': resp})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/autosell/status', methods=['GET'])
def api_autosell_status():
    """Get auto-sell monitor status."""
    try:
        status = get_auto_sell_status()
        # Verify process is still alive
        if status['running'] and status.get('pid'):
            if not is_process_alive(status['pid']):
                # Process died, update status
                set_auto_sell_status(False)
                status['running'] = False
        
        # Include current bot state for monitoring display
        bot_state = read_state()
        status.update({
            'current_bid': bot_state.get('bid', 0),
            'volume': bot_state.get('volume', 0),
            'buy_price': bot_state.get('buy_price', 0),
            'current_value_ngn': bot_state.get('current_value_ngn', 0),
            'profit_ngn': bot_state.get('profit_ngn', 0),
            'profit_pct': bot_state.get('profit_pct', 0),
            'pair': bot_state.get('pair', 'USDTNGN'),
        })
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/autosell/start', methods=['POST'])
def api_autosell_start():
    """Start auto-sell monitor process."""
    try:
        with _auto_sell_lock:
            data = request.get_json() or {}
            target_pct = float(data.get('target_pct', 2.0))
            pair = (data.get('pair') or os.getenv('PAIR') or '').upper()
            
            # Check if already running
            status = get_auto_sell_status()
            if status['running'] and status.get('pid') and is_process_alive(status['pid']):
                return jsonify({'success': False, 'error': 'Auto-sell already running (PID: {})'.format(status['pid'])}), 400
            
            # Start new auto-sell monitor process using current Python interpreter
            proc = subprocess.Popen(
                [sys.executable, "auto_sell_monitor.py"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            
            # Save PID and target to state file (auto_sell_monitor.py reads from .env)
            set_auto_sell_status(True, proc.pid, target_pct)
            
            # Also update .env with target and optional PAIR so the monitor knows which pair to watch
            cfg = dotenv_values('.env')
            cfg['AUTO_SELL_TARGET_PCT'] = str(target_pct)
            if pair:
                cfg['PAIR'] = pair
            with open('.env', 'w') as f:
                for k, v in cfg.items():
                    f.write(f"{k}={v}\n")
            
            return jsonify({'success': True, 'message': f'Auto-sell started (PID: {proc.pid})', 'pid': proc.pid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/autosell/hold', methods=['POST'])
def api_autosell_hold():
    """Hold or unhold a specific pair from being auto-sold.
    Request JSON: { "pair": "SOLNGN", "hold": true }
    """
    try:
        data = request.get_json() or {}
        pair = (data.get('pair') or '').strip().upper()
        hold = bool(data.get('hold'))

        if not pair:
            return jsonify({'success': False, 'error': 'pair_required', 'message': 'pair is required (e.g. SOLNGN)'}), 400

        ok = set_hold_for_pair(pair, hold)
        if not ok:
            return jsonify({'success': False, 'error': 'failed', 'message': 'Could not set hold status'}), 500

        return jsonify({'success': True, 'pair': pair, 'held': hold})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/autosell/holds', methods=['GET'])
def api_autosell_holds():
    try:
        held = get_held_pairs()
        return jsonify({'success': True, 'held_pairs': held})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/autosell/sell-now', methods=['POST'])
def api_autosell_sell_now():
    """Immediately sell all available balance of a specified asset."""
    try:
        data = request.get_json() or {}
        pair = (data.get('pair') or 'USDTNGN').upper()
        
        # Validate pair format - should be like SOLNGN, XBTNGN, etc. not just SOL or XBT
        if len(pair) < 5:
            return jsonify({'success': False, 'error': 'invalid_pair_format', 'message': f'Invalid pair format: {pair}. Use format like SOLNGN, XBTNGN, USDTNGN (Asset + Quote). For example, to sell SOL use SOLNGN.'}), 400
        
        # debug log
        try:
            with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write(f"[AUTOSELL] sell-now called for pair={pair}\n")
        except Exception:
            pass

        # Get current user credentials
        api_key, api_secret, user = get_request_credentials(require_user_keys=True)
        if user and (not api_key or not api_secret):
            try:
                with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                    dbg.write('[AUTOSELL] no user keys available\n')
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'no_user_keys', 'message': 'enter your luno account api & secret in Credentials to have full access.'}), 400

        # Extract base asset from pair (e.g. USDT from USDTNGN)
        known_quotes = ['USDT', 'USDC', 'NGN', 'ZAR', 'USD', 'EUR', 'GBP', 'XBT', 'BTC']
        base_asset = None
        for q in known_quotes:
            if pair.endswith(q):
                base_asset = pair[:-len(q)]
                break
        
        if not base_asset:
            base_asset = pair[:3]  # fallback

        # Fetch current balance for the base asset
        import requests
        try:
            with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write('[AUTOSELL] fetching balance from Luno API\n')
        except Exception:
            pass

        try:
            resp = requests.get('https://api.luno.com/api/1/balance', auth=(api_key, api_secret), timeout=10)
            resp.raise_for_status()
            balance_data = resp.json()
            balances = balance_data.get('balance', [])
            
            available = 0.0
            for item in balances:
                if item.get('asset') == base_asset:
                    available = float(item.get('balance', 0)) - float(item.get('reserved', 0))
                    break
            
            if available <= 0:
                try:
                    with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                        dbg.write(f"[AUTOSELL] no available {base_asset} to sell (available={available})\n")
                except Exception:
                    pass
                return jsonify({'success': False, 'error': 'insufficient_balance', 'message': f'No available {base_asset} to sell'}), 400
            
        except Exception as e:
            return jsonify({'success': False, 'error': 'balance_fetch_failed', 'message': str(e)}), 400

        # Get current ticker price
        client = LunoClient(api_key, api_secret, dry_run=False)
        try:
            with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write(f"[AUTOSELL] available to sell: {available} {base_asset}\n")
        except Exception:
            pass

        try:
            ticker = client.get_ticker(pair)
            bid = float(ticker.get('bid') or ticker.get('last') or 0)
            
            if bid <= 0:
                return jsonify({'success': False, 'error': 'invalid_price', 'message': f'Invalid bid price: {bid}'}), 400
            
        except Exception as e:
            err_str = str(e)
            # Check for various error indicators that suggest invalid pair
            if any(x in err_str for x in ['400', 'Bad Request', 'Client Error', 'not supported']):
                # Likely invalid pair format - suggest correct format
                suggested_pair = f"{pair}NGN" if not pair.endswith('NGN') and len(pair) <= 4 else pair
                return jsonify({
                    'success': False,
                    'error': 'invalid_pair',
                    'message': f'Pair "{pair}" is not supported by Luno or in an invalid format.\n\nUse the format: ASSETNGN\n\nExamples:\n• SOLNGN (for SOL)\n• XBTNGN (for Bitcoin)\n• ETHNGN (for Ethereum)\n• USDTNGN (for USDT)',
                    'suggestion': suggested_pair,
                    'common_pairs': ['USDTNGN', 'USDCNGN', 'XBTNGN', 'ETHNGN', 'SOLNGN', 'ATOMNGN', 'LITNGN', 'XRPNGN']
                }), 400
            return jsonify({'success': False, 'error': 'ticker_fetch_failed', 'message': str(e)}), 400

        # Place sell order
        try:
            try:
                with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                    dbg.write(f"[AUTOSELL] ticker bid={bid}, placing sell for {available} {base_asset}\n")
            except Exception:
                pass

            sell_price = bid * 0.99  # Sell slightly below bid for faster execution
            # Check minimum order volume for this pair to avoid API rejections
            min_vol = get_min_volume_for_pair(pair)
            if available < min_vol:
                error_msg = f'❌ Insufficient balance: You have {available:.8f} {base_asset} but need at least {min_vol} {base_asset} to sell on {pair}. Please wait for more funds or consolidate.'
                try:
                    with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                        dbg.write(f"[AUTOSELL] VOLUME_TOO_SMALL: available={available}, minimum={min_vol} for {pair}\n")
                except Exception:
                    pass
                return jsonify({'success': False, 'error': 'volume_too_small', 'message': error_msg}), 400

            resp = client.place_order(
                pair=pair,
                side='sell',
                volume=round(available, 8),
                price=sell_price,
                order_type='limit'
            )
            
            order_id = resp.get('order_id', 'unknown')
            expected_ngn = available * sell_price
            
            # Log the trade
            append_trade_log_row(
                datetime.now().timestamp(),
                pair,
                'SELL',
                sell_price,
                available,
                details={'order_resp': resp, 'auto_sell': True}
            )
            
            return jsonify({
                'success': True,
                'message': f'✅ Sell order placed!',
                'order_id': order_id,
                'pair': pair,
                'asset': base_asset,
                'volume': available,
                'price': sell_price,
                'expected_ngn': round(expected_ngn, 2)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': 'order_failed', 'message': str(e)}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/debug/postorder', methods=['GET'])
def api_debug_postorder():
    """Run the local `postorder_debug.py` script and return its stdout/stderr.
    This helps capture the exact Luno API response body for debugging 400 errors.
    Only available on local dev servers (not for public deployment).
    """
    try:
        # Run the debug script using the same Python interpreter
        proc = subprocess.run([sys.executable, 'postorder_debug.py'], cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True, timeout=30)
        return jsonify({
            'success': True,
            'returncode': proc.returncode,
            'stdout': proc.stdout.splitlines()[-200:],
            'stderr': proc.stderr.splitlines()[-200:],
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'postorder_debug timed out after 30s'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/autosell/stop', methods=['POST'])
def api_autosell_stop():
    """Stop auto-sell monitor process."""
    try:
        with _auto_sell_lock:
            status = get_auto_sell_status()
            pid = status.get('pid')
            
            if not status['running'] or not pid:
                return jsonify({'success': False, 'error': 'Auto-sell not running'}), 400
            
            # Try to terminate process
            try:
                if is_process_alive(pid):
                    proc = psutil.Process(pid)
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
            except (psutil.NoSuchProcess, ProcessLookupError):
                pass
            
            set_auto_sell_status(False)
            return jsonify({'success': True, 'message': 'Auto-sell stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def _start_auto_sell_process(pair: str = None, target_pct: float = 2.0):
    """Helper to start the auto_sell_monitor.py subprocess and persist state/.env."""
    with _auto_sell_lock:
        cfg = dotenv_values('.env')
        if pair:
            cfg['PAIR'] = pair
        cfg['AUTO_SELL_TARGET_PCT'] = str(target_pct)

        # write .env
        try:
            with open('.env', 'w') as f:
                for k, v in cfg.items():
                    f.write(f"{k}={v}\n")
        except Exception:
            pass

        proc = subprocess.Popen([
            sys.executable, 'auto_sell_monitor.py'
        ], cwd=os.path.dirname(os.path.abspath(__file__)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        set_auto_sell_status(True, proc.pid, target_pct)
        try:
            with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write(f"[WATCHDOG] started auto_sell_monitor PID={proc.pid} pair={pair} target={target_pct}\n")
        except Exception:
            pass
        return proc.pid


def auto_sell_watchdog_loop():
    """Background watchdog that ensures the auto-sell monitor is running.
    If the monitor exits, this will restart it and update state.
    """
    try:
        while True:
            try:
                status = get_auto_sell_status()
                running = status.get('running') and status.get('pid') and is_process_alive(status.get('pid'))
                if not running:
                    # Start monitor using PAIR and target from .env
                    cfg = dotenv_values('.env')
                    pair = (cfg.get('PAIR') or cfg.get('TRADING_PAIR') or '').upper()
                    target = float(cfg.get('AUTO_SELL_TARGET_PCT') or 2.0)
                    pid = _start_auto_sell_process(pair or None, target)
                # Sleep before next check
            except Exception as e:
                try:
                    with open('autosell_debug.log', 'a', encoding='utf-8') as dbg:
                        dbg.write(f"[WATCHDOG] error: {e}\n")
                except Exception:
                    pass
            time.sleep(10)
    except Exception:
        pass


def start_watchdog_thread():
    t = threading.Thread(target=auto_sell_watchdog_loop, daemon=True)
    t.start()


# Start the watchdog to ensure the auto-sell monitor remains running
try:
    start_watchdog_thread()
except Exception as _e:
    print(f"Failed to start auto-sell watchdog: {_e}")


def save_credentials_to_env(api_key, api_secret, pair=None, dry_run=None):
    """Save credentials to .env file and trigger auto-reload."""
    try:
        env_path = ".env"
        env_vars = {}
        
        # Read existing .env file
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
        
        # Update credentials
        if api_key:
            env_vars["LUNO_API_KEY"] = api_key
        if api_secret:
            env_vars["LUNO_API_SECRET"] = api_secret
        if pair:
            env_vars["TRADING_PAIR"] = pair
        if dry_run is not None:
            env_vars["DRY_RUN"] = "true" if dry_run else "false"
        
        # Write updated .env file
        with open(env_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Credentials saved to .env - credential_monitor will auto-reload")
        return True
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False


@app.route("/api/credentials/get", methods=['GET'])
def api_credentials_get():
    """Get current credentials (masked)."""
    try:
        # Prefer per-user stored credentials. If the logged-in user has no keys,
        # instruct them to add their Luno API keys to gain full access.
        api_key, api_secret, user = get_request_credentials(require_user_keys=False)

        if user and (not api_key or not api_secret):
            return jsonify({'success': False, 'error': 'no_user_keys', 'message': 'enter your luno account api & secret in Credentials to have full access.'}), 200

        # If we have keys (either user or global), mask them and return.
        api_key = api_key or ''
        api_secret = api_secret or ''
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else (api_key and "****")
        masked_secret = api_secret[:4] + "*" * (len(api_secret) - 8) + api_secret[-4:] if len(api_secret) > 8 else (api_secret and "****")

        # Determine pair and dry_run from .env fallback (legacy settings)
        from dotenv import dotenv_values
        cfg = dotenv_values('.env')
        return jsonify({
            'success': True,
            'api_key': masked_key,
            'api_secret': masked_secret,
            'pair': cfg.get('TRADING_PAIR', 'XBTNGN'),
            'dry_run': cfg.get('DRY_RUN', 'true').lower() == 'true',
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/api/credentials/save", methods=['POST'])
def api_credentials_save():
    """Save Luno credentials and trigger auto-reload."""
    try:
        # Save per-user credentials into the DB. Users must be logged in.
        data = request.get_json() or {}
        api_key = (data.get('api_key') or '').strip()
        api_secret = (data.get('api_secret') or '').strip()
        pair = (data.get('pair') or '').strip()

        if not session.get('user_id'):
            return jsonify({'success': False, 'error': 'authentication required'}), 401

        if not api_key or not api_secret:
            return jsonify({'success': False, 'error': 'API key and secret are required'}), 400

        s = get_session()
        user = s.query(User).filter_by(id=session.get('user_id')).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        user.luno_api_key = api_key
        user.luno_api_secret = api_secret
        s.add(user)
        s.commit()

        return jsonify({
            'success': True,
            'message': 'Credentials saved to your account. You now have full access.',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route("/api/credentials/validate", methods=['POST'])
def api_credentials_validate():
    """Validate credentials before saving."""
    try:
        from luno_client import LunoClient
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
            
        api_key = data.get('api_key', '').strip()
        api_secret = data.get('api_secret', '').strip()
        pair = data.get('pair', 'XBTNGN').strip()
        
        if not api_key or not api_secret:
            return jsonify({'success': False, 'error': 'API key and secret required'}), 400
        
        try:
            test_client = LunoClient(api_key, api_secret)
            ticker = test_client.get_ticker(pair)

            if ticker and ('last_trade' in ticker or 'last' in ticker):
                price = ticker.get('last_trade') or ticker.get('last') or 'N/A'
                msg = f'✅ Connected! Pair {pair} price: {price}'
                return jsonify({'success': True, 'message': msg})
            else:
                return jsonify({'success': False, 'error': 'Invalid ticker response'}), 400

        except Exception as e:
            print(f'[VALIDATION] Error for {api_key}: {str(e)}')
            return jsonify({'success': False, 'error': f'Validation failed: {str(e)}'}), 400
            
    except Exception as e:
        print(f'[VALIDATION] Server error: {str(e)}')
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route("/api/account/balances", methods=['GET'])
def api_account_balances():
    """Get account balances using Luno /balance endpoint."""
    try:
        # Use per-user credentials whenever possible and require them for account endpoints.
        api_key, api_secret, user = get_request_credentials(require_user_keys=True)

        if user and (not api_key or not api_secret):
            return jsonify({'success': False, 'error': 'no_user_keys', 'message': 'enter your luno account api & secret in Credentials to have full access.'}), 400

        # Fetch balances directly from Luno /balance endpoint
        try:
            import requests
            resp = requests.get('https://api.luno.com/api/1/balance', auth=(api_key, api_secret), timeout=10)
            resp.raise_for_status()
            balance_data = resp.json()
            
            # Parse the balance list
            balances_list = balance_data.get('balance', [])
            formatted_balances = []
            
            for item in balances_list:
                formatted_balances.append({
                    'account_id': item.get('account_id'),
                    'asset': item.get('asset', 'N/A'),
                    'balance': float(item.get('balance', 0)),
                    'reserved': float(item.get('reserved', 0)),
                    'unconfirmed': float(item.get('unconfirmed', 0)),
                    'available': float(item.get('balance', 0)) - float(item.get('reserved', 0))
                })
            
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'balances': formatted_balances,
                'message': f'✅ Loaded {len(formatted_balances)} account balances'
            })
            
        except requests.exceptions.RequestException as e:
            print(f'[BALANCES] Luno API error: {str(e)}')
            return jsonify({'success': False, 'error': f'Failed to fetch balances: {str(e)}'}), 400
            
    except Exception as e:
        print(f'[BALANCES] Server error: {str(e)}')
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/api/account/wallet', methods=['GET'])
def api_account_wallet():
    """Return raw wallet balances with computed available amounts (balance - reserved).
    This helps clients discover which base assets (BTC/XBT, ETH, USDT, etc.) are available.
    """
    try:
        from luno_client import LunoClient
        api_key, api_secret, user = get_request_credentials(require_user_keys=True)

        if user and (not api_key or not api_secret):
            return jsonify({'success': False, 'error': 'no_user_keys', 'message': 'enter your luno account api & secret in Credentials to have full access.'}), 400

        client = LunoClient(api_key, api_secret)
        balances_resp = client.get_balances()
        wallet = balances_resp.get('wallet', []) if isinstance(balances_resp, dict) else []

        out = []
        for asset in wallet:
            bal = float(asset.get('balance', 0) or 0)
            reserved = float(asset.get('reserved', 0) or 0)
            available = round(bal - reserved, 8)
            out.append({
                'asset': asset.get('asset'),
                'balance': bal,
                'reserved': reserved,
                'available': available,
                'total': round(bal + reserved, 8)
            })

        # Also include a quick map for common base assets (XBT, BTC alias handling)
        # Normalize XBT/BTC naming conservatively
        for item in out:
            if item['asset'] == 'XBT':
                item['aliases'] = ['BTC']

        return jsonify({'success': True, 'wallet': out})

    except Exception as e:
        print(f'[WALLET] Error fetching wallet: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# TRADINGVIEW WEBHOOK ENDPOINTS
# ============================================================================

def log_tradingview_alert(signal: str, pair: str, status: str, message: str = ""):
    """Log TradingView alerts to a file for audit trail."""
    try:
        log_file = "tradingview_alerts.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] SIGNAL={signal} | PAIR={pair} | STATUS={status} | {message}\n"
        with open(log_file, 'a') as f:
            f.write(log_line)
        print(f"[TV-WEBHOOK] {log_line.strip()}")
    except Exception as e:
        print(f"[TV-WEBHOOK] Error writing log: {e}")


def handle_buy_signal(pair: str, volume: float = None) -> dict:
    """Handle BUY signal from TradingView: place a limit buy order on Luno."""
    try:
        config = dotenv_values(".env")
        api_key = config.get("LUNO_API_KEY", "")
        api_secret = config.get("LUNO_API_SECRET", "")
        
        if not api_key or not api_secret:
            msg = "❌ Luno API credentials not configured"
            log_tradingview_alert("BUY", pair, "FAILED", msg)
            return {
                "status": "error",
                "message": msg,
                "pair": pair,
                "signal": "buy"
            }
        
        # Get volume from env or use default
        if volume is None:
            volume = float(config.get("VOLUME", 0.001))
        
        # Create Luno client and get current ticker for price
        client = LunoClient(api_key, api_secret, dry_run=False)
        ticker = client.get_ticker(pair)
        last_price = float(ticker.get('last_trade', 0))
        
        if last_price <= 0:
            msg = f"❌ Invalid price from ticker: {last_price}"
            log_tradingview_alert("BUY", pair, "FAILED", msg)
            return {
                "status": "error",
                "message": msg,
                "pair": pair,
                "signal": "buy"
            }
        
        # Place BUY order at current market price (limit order just below market)
        buy_price = last_price * 0.99  # Buy at 1% below current price
        print(f"[TV-WEBHOOK] Placing BUY order for {pair}: volume={volume}, price={buy_price}")
        
        order_resp = client.place_order(
            pair=pair,
            side="buy",
            volume=volume,
            price=buy_price,
            order_type="limit"
        )
        
        order_id = order_resp.get("order_id", "unknown")
        msg = f"✅ BUY order placed successfully | OrderID: {order_id} | Pair: {pair} | Volume: {volume} | Price: {buy_price}"
        log_tradingview_alert("BUY", pair, "SUCCESS", f"OrderID={order_id}, Volume={volume}, Price={buy_price}")
        
        return {
            "status": "ok",
            "message": msg,
            "pair": pair,
            "signal": "buy",
            "order_id": order_id,
            "volume": volume,
            "price": buy_price
        }
        
    except Exception as e:
        msg = f"❌ Error placing BUY order: {str(e)}"
        log_tradingview_alert("BUY", pair, "FAILED", str(e))
        print(f"[TV-WEBHOOK] {msg}")
        return {
            "status": "error",
            "message": msg,
            "pair": pair,
            "signal": "buy",
            "error": str(e)
        }


def handle_sell_signal(pair: str, volume: float = None) -> dict:
    """Handle SELL signal from TradingView: place a limit sell order on Luno."""
    try:
        config = dotenv_values(".env")
        api_key = config.get("LUNO_API_KEY", "")
        api_secret = config.get("LUNO_API_SECRET", "")
        
        if not api_key or not api_secret:
            msg = "❌ Luno API credentials not configured"
            log_tradingview_alert("SELL", pair, "FAILED", msg)
            return {
                "status": "error",
                "message": msg,
                "pair": pair,
                "signal": "sell"
            }
        
        # Get volume from env or use default
        if volume is None:
            volume = float(config.get("VOLUME", 0.001))
        
        # Create Luno client and get current ticker for price
        client = LunoClient(api_key, api_secret, dry_run=False)
        ticker = client.get_ticker(pair)
        last_price = float(ticker.get('last_trade', 0))
        
        if last_price <= 0:
            msg = f"❌ Invalid price from ticker: {last_price}"
            log_tradingview_alert("SELL", pair, "FAILED", msg)
            return {
                "status": "error",
                "message": msg,
                "pair": pair,
                "signal": "sell"
            }
        
        # Place SELL order at current market price (limit order just above market)
    # Before placing the sell, check available balance for the base asset so we can return
    # a helpful error instead of letting the exchange return a generic 'insufficient balance'.
        try:
            # Detect common quote symbols to extract base asset (e.g. XBTNGN -> XBT)
            known_quotes = ['USDT', 'USDC', 'NGN', 'ZAR', 'USD', 'EUR', 'GBP']
            quote = None
            for q in known_quotes:
                if pair.endswith(q):
                    quote = q
                    break
            if quote:
                base_asset = pair[:-len(quote)]
            else:
                # Fallback to first 3 characters if unknown
                base_asset = pair[:3]

            balances_resp = client.get_balances()
            wallet = balances_resp.get('wallet', [])
            available_amount = 0.0
            for asset in wallet:
                if asset.get('asset') == base_asset:
                    bal = float(asset.get('balance', 0) or 0)
                    reserved = float(asset.get('reserved', 0) or 0)
                    available_amount = bal - reserved
                    break

            # If volume wasn't provided, default to selling the full available amount
            if volume is None:
                volume = round(available_amount, 8)

            if available_amount <= 0:
                msg = f"❌ No available balance to sell: available {available_amount} {base_asset}"
                log_tradingview_alert("SELL", pair, "FAILED", msg)
                print(f"[TV-WEBHOOK] {msg}")
                return {
                    "status": "error",
                    "message": msg,
                    "pair": pair,
                    "signal": "sell",
                    "available": available_amount,
                    "asset": base_asset
                }

            if available_amount < float(volume):
                msg = f"❌ Insufficient balance to place this order: available {available_amount} {base_asset}, requested {volume}"
                log_tradingview_alert("SELL", pair, "FAILED", msg)
                print(f"[TV-WEBHOOK] {msg}")
                return {
                    "status": "error",
                    "message": msg,
                    "pair": pair,
                    "signal": "sell",
                    "available": available_amount,
                    "asset": base_asset
                }
        except Exception as e:
            # If balances cannot be fetched for any reason, continue to attempt the order
            # but log the exception to help debugging.
            print(f"[TV-WEBHOOK] Could not fetch balances for pre-check: {e}")

        sell_price = last_price * 1.01  # Sell at 1% above current price
        print(f"[TV-WEBHOOK] Placing SELL order for {pair}: volume={volume}, price={sell_price}")

        order_resp = client.place_order(
            pair=pair,
            side="sell",
            volume=volume,
            price=sell_price,
            order_type="limit"
        )
        
        order_id = order_resp.get("order_id", "unknown")
        msg = f"✅ SELL order placed successfully | OrderID: {order_id} | Pair: {pair} | Volume: {volume} | Price: {sell_price}"
        log_tradingview_alert("SELL", pair, "SUCCESS", f"OrderID={order_id}, Volume={volume}, Price={sell_price}")
        
        return {
            "status": "ok",
            "message": msg,
            "pair": pair,
            "signal": "sell",
            "order_id": order_id,
            "volume": volume,
            "price": sell_price
        }
        
    except Exception as e:
        msg = f"❌ Error placing SELL order: {str(e)}"
        log_tradingview_alert("SELL", pair, "FAILED", str(e))
        print(f"[TV-WEBHOOK] {msg}")
        return {
            "status": "error",
            "message": msg,
            "pair": pair,
            "signal": "sell",
            "error": str(e)
        }


@app.route("/tv-webhook", methods=["POST"])
def tradingview_webhook():
    """
    TradingView webhook endpoint for automated trading signals.
    
    Expects JSON POST:
    {
        "signal": "buy" or "sell",
        "pair": "XBTNGN",
        "volume": 0.001  (optional)
    }
    
    Returns JSON:
    {
        "status": "ok" or "error",
        "message": "...",
        "order_id": "...",
        ...
    }
    """
    try:
        # Parse incoming JSON
        data = request.get_json(force=True)
        
        if not data:
            msg = "❌ No JSON data received"
            log_tradingview_alert("UNKNOWN", "UNKNOWN", "FAILED", msg)
            return jsonify({
                "status": "error",
                "message": msg
            }), 400

        signal = data.get("signal", "").lower().strip()
        pair = (data.get("pair", "") or "").upper().strip()
        volume = data.get("volume")
        
        print(f"\n[TV-WEBHOOK] Received alert: signal={signal}, pair={pair}, volume={volume}")
        
        # Webhook token check (optional): if TV_WEBHOOK_TOKEN is set in env, require it.
        tv_token_env = os.getenv('TV_WEBHOOK_TOKEN')
        if tv_token_env:
            # Accept token via query param ?token=, header X-TV-Token, or JSON body 'token'
            req_token = request.args.get('token') or request.headers.get('X-TV-Token') or data.get('token')
            if not req_token or str(req_token) != str(tv_token_env):
                msg = "❌ Invalid or missing webhook token"
                log_tradingview_alert('UNKNOWN', data.get('pair', 'UNKNOWN'), 'FAILED', msg)
                return jsonify({
                    "status": "error",
                    "message": msg
                }), 403

        # Validate signal
        if signal not in ("buy", "sell"):
            msg = f"❌ Invalid signal: '{signal}'. Must be 'buy' or 'sell'."
            log_tradingview_alert(signal, pair, "FAILED", msg)
            return jsonify({
                "status": "error",
                "message": msg
            }), 400
        
        # If pair is missing or does not include a quote currency (e.g. 'ETH' instead of 'ETHNGN'),
        # try to resolve a full pair automatically by preferring quote currencies with balances
        if not pair:
            # attempt to resolve from env/strategy and available wallets
            pair = None
        # Helper: resolve pair when needed
        def _resolve_pair(pair_hint=None):
            """Resolve a full trading pair string. If pair_hint already contains a known quote
            (USDT, USDC, NGN, etc.) it is returned as-is. Otherwise, pick a quote that has
            available balance (prefer USDT -> USDC -> NGN). Falls back to TRADING_PAIR or NGN.
            """
            from luno_client import LunoClient
            cfg = dotenv_values('.env')
            api_key = cfg.get('LUNO_API_KEY', '')
            api_secret = cfg.get('LUNO_API_SECRET', '')

            # Allow configuring quote priority via saved state (settings.quote_priority)
            st = read_state()
            settings = st.get('settings', {}) if isinstance(st, dict) else {}
            known_quotes = settings.get('quote_priority') or ['USDT', 'USDC', 'NGN', 'ZAR', 'USD', 'EUR', 'GBP']
            # If hint already contains a quote, return it
            if pair_hint:
                ph = pair_hint.upper()
                for q in known_quotes:
                    if ph.endswith(q):
                        return ph
                base = ph
            else:
                # Try configured TRADING_PAIR or strategy active coin
                tp = cfg.get('TRADING_PAIR') or strategy.get_active_coin() or ''
                tp = tp.upper()
                for q in known_quotes:
                    if tp.endswith(q):
                        return tp
                # If tp doesn't include a quote, treat tp as base
                base = tp or 'XBT'

            # Try to pick a quote with available balance
            try:
                client = LunoClient(api_key, api_secret, dry_run=True)
                balances_resp = client.get_balances()
                wallet = balances_resp.get('wallet', []) if isinstance(balances_resp, dict) else []
                for q in known_quotes:
                    for asset in wallet:
                        if asset.get('asset') == q:
                            bal = float(asset.get('balance', 0) or 0)
                            reserved = float(asset.get('reserved', 0) or 0)
                            if (bal - reserved) > 0:
                                return (base + q).upper()
            except Exception:
                # If balances can't be fetched, fall back to env or NGN
                pass

            if cfg.get('TRADING_PAIR'):
                return cfg.get('TRADING_PAIR').upper()
            return (base + 'NGN').upper()

        # Resolve pair now if necessary
        if not pair or not any(pair.endswith(q) for q in ['USDT', 'USDC', 'NGN', 'ZAR', 'USD', 'EUR', 'GBP']):
            try:
                pair = _resolve_pair(pair)
            except Exception as e:
                msg = f"❌ Could not resolve trading pair: {e}"
                log_tradingview_alert(signal, pair or 'UNKNOWN', "FAILED", msg)
                return jsonify({"status": "error", "message": msg}), 400
        
        # Validate volume if provided
        if volume is not None:
            try:
                volume = float(volume)
                if volume <= 0:
                    raise ValueError("Volume must be positive")
            except (ValueError, TypeError) as e:
                msg = f"❌ Invalid volume: {str(e)}"
                log_tradingview_alert(signal, pair, "FAILED", msg)
                return jsonify({
                    "status": "error",
                    "message": msg
                }), 400
        
        # Execute appropriate signal handler
        if signal == "buy":
            result = handle_buy_signal(pair, volume)
        else:  # signal == "sell"
            result = handle_sell_signal(pair, volume)
        
        # Return response
        # Persist last TV webhook info for dashboard UI and status checks
        try:
            update_tradingview_state({
                'last_seen': datetime.now().isoformat(),
                'signal': signal,
                'requested_pair': data.get('pair'),
                'resolved_pair': pair,
                'volume': volume,
                'result_status': result.get('status')
            })
        except Exception:
            pass

        status_code = 200 if result.get("status") == "ok" else 400
        return jsonify(result), status_code
        
    except Exception as e:
        msg = f"❌ Webhook error: {str(e)}"
        print(f"[TV-WEBHOOK] {msg}")
        log_tradingview_alert("ERROR", "ERROR", "FAILED", str(e))
        return jsonify({
            "status": "error",
            "message": msg,
            "error": str(e)
        }), 500


@app.route("/tv-webhook/status", methods=["GET"])
def tradingview_webhook_status():
    """Health check endpoint for TradingView webhook."""
    try:
        # Check if credentials are configured
        config = dotenv_values(".env")
        has_credentials = bool(config.get("LUNO_API_KEY")) and bool(config.get("LUNO_API_SECRET"))
        
        # Try to ping Luno API
        luno_status = "unknown"
        try:
            from luno_client import LunoClient
            client = LunoClient(
                config.get("LUNO_API_KEY", ""),
                config.get("LUNO_API_SECRET", ""),
                dry_run=True
            )
            pair = config.get("TRADING_PAIR", "XBTNGN")
            ticker = client.get_ticker(pair)
            luno_status = "ok"
        except Exception as e:
            luno_status = f"error: {str(e)}"
        
        return jsonify({
            "status": "healthy",
            "webhook_endpoint": "/tv-webhook",
            "credentials_configured": has_credentials,
            "luno_api_status": luno_status,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/tradingview/status', methods=['GET'])
def api_tradingview_status():
    """Return the last TradingView webhook metadata (last_seen, signal, resolved_pair, etc.)."""
    try:
        st = read_state()
        tv = st.get('tradingview', {})
        # Determine active if last_seen within 10 minutes
        active = False
        last_seen = tv.get('last_seen')
        if last_seen:
            try:
                dt = datetime.fromisoformat(last_seen)
                delta = datetime.now() - dt
                active = delta.total_seconds() <= 600
            except Exception:
                active = True
        return jsonify({'success': True, 'tradingview': tv, 'active': active}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/healthz', methods=['GET'])
def healthz():
    """Simple health endpoint for process managers and load balancers."""
    try:
        return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200
    except Exception:
        return jsonify({'status': 'error'}), 500


@app.route('/api/settings/quote_priority', methods=['GET', 'POST'])
def api_settings_quote_priority():
    """Get or set the quote priority list used for automatic pair resolution.
    GET returns { success: True, quote_priority: [...] }
    POST expects JSON { quote_priority: ["USDT","NGN",...] }
    """
    try:
        if request.method == 'GET':
            st = read_state()
            settings = st.get('settings', {}) if isinstance(st, dict) else {}
            qp = settings.get('quote_priority') or ['USDT', 'USDC', 'NGN', 'ZAR', 'USD', 'EUR', 'GBP']
            return jsonify({'success': True, 'quote_priority': qp}), 200

        # POST - update
        data = request.get_json() or {}
        qp = data.get('quote_priority')
        if not isinstance(qp, list) or not all(isinstance(x, str) for x in qp):
            return jsonify({'success': False, 'error': 'quote_priority must be an array of strings'}), 400

        # Save into state
        st = read_state()
        if not isinstance(st, dict):
            st = {}
        settings = st.get('settings', {})
        settings['quote_priority'] = [s.upper() for s in qp]
        st['settings'] = settings
        write_state(st)
        return jsonify({'success': True, 'quote_priority': settings['quote_priority']}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == "__main__":
    print("Dashboard running at http://localhost:5000")
    try:
        # Diagnostic: print registered URL rules to help debug missing routes
        print("Registered routes:")
        for rule in sorted(list(app.url_map.iter_rules()), key=lambda r: r.rule):
            methods = ','.join(sorted(rule.methods))
            print(f"  {rule.rule} -> methods: {methods}")
    except Exception as e:
        print(f"Error printing url_map: {e}")
    app.run(debug=True, port=5000, use_reloader=False)
