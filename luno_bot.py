"""Simple rule-based Luno trading bot.

- Reads config from environment or .env
- Uses `LunoClient` (dry-run by default)
- Logs trades to CSV
- Writes state to bot_state.json for dashboard

This is a template. Add risk controls and test on small amounts / sandbox before going live.
"""

import os
import time
import json
from collections import deque
from datetime import datetime

import strategy
from utils import retry_with_backoff
import logging
import argparse
import csv
from decimal import Decimal

from dotenv import load_dotenv
from luno_client import LunoClient
from credential_monitor import initialize_monitor, get_monitor, has_valid_credentials

# Load .env if present
load_dotenv()

# Initialize credential monitor (watches for changes)
monitor = initialize_monitor(".env", check_interval=5)

LOGGER = logging.getLogger("luno_bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# Also write logs to a file so the dashboard can tail them
LOG_FILE = os.getenv('BOT_LOG_FILE', 'bot.log')
try:
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(fh)
except Exception:
    # If file handler creation fails, continue with console logging only
    pass


def read_config():
    """Read config from .env (auto-reloads if credentials change)."""
    # Get credentials from monitor (checks for .env updates)
    creds = get_monitor().get_credentials()
    
    cfg = {
        "api_key": creds["api_key"],
        "api_secret": creds["api_secret"],
        "pair": creds.get("pair", os.getenv("PAIR", "XBTUSD")),
        "buy_target": Decimal(os.getenv("BUY_TARGET", "0")),
        "sell_target": Decimal(os.getenv("SELL_TARGET", "0")),
        "volume": Decimal(os.getenv("VOLUME", "0.0")),
        "interval": int(os.getenv("INTERVAL", "30")),
        "dry_run": creds.get("dry_run", os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")),
        "log_csv": os.getenv("LOG_CSV", "trade_log.csv"),
    }
    return cfg


def append_trade_log(csv_path, row):
    header = ["timestamp", "pair", "action", "price", "volume", "details"]
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)


def write_state(state_file, state):
    """Write bot state to JSON for dashboard to read."""
    with open(state_file, "w") as f:
        json.dump(state, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one loop iteration and exit")
    args = parser.parse_args()

    cfg = read_config()
    if not cfg["api_key"] or not cfg["api_secret"]:
        LOGGER.warning("LUNO_API_KEY and LUNO_API_SECRET are not set. The client will still run in dry-run mode if DRY_RUN=true.")

    client = LunoClient(cfg["api_key"], cfg["api_secret"], dry_run=cfg["dry_run"])

    LOGGER.info("Starting bot: pair=%s buy_target=%s sell_target=%s volume=%s dry_run=%s", cfg["pair"], cfg["buy_target"], cfg["sell_target"], cfg["volume"], cfg["dry_run"])

    # Rolling buffer for prices (useful for TA calculations). Period controlled via ENV: EMA_PERIOD
    ema_period = int(os.getenv("EMA_PERIOD", "10"))
    buffer_size = max(ema_period * 2, 20)
    prices = deque(maxlen=buffer_size)
    state = {
        "last_price": 0,
        "pair": cfg["pair"],
        "dry_run": cfg["dry_run"],
        "last_update": datetime.now().isoformat(),
        "prices": [],
        "balance": {},
    }
    
    # Track last config for change detection
    last_config = cfg.copy()

    try:
        while True:
            try:
                # Check if credentials changed in .env file
                if get_monitor().check_for_updates():
                    new_cfg = read_config()
                    
                    # Reinitialize client if API key/secret changed
                    if (new_cfg["api_key"] != last_config["api_key"] or 
                        new_cfg["api_secret"] != last_config["api_secret"]):
                        LOGGER.info("🔄 API credentials changed, reinitializing client...")
                        client = LunoClient(new_cfg["api_key"], new_cfg["api_secret"], dry_run=new_cfg["dry_run"])
                        LOGGER.info("✅ Client reinitialized with new credentials")
                    
                    # If pair changed, clear price history
                    if new_cfg["pair"] != last_config["pair"]:
                        LOGGER.info("🔄 Trading pair changed from %s to %s, clearing price history", last_config["pair"], new_cfg["pair"])
                        prices.clear()
                    
                    # Update config
                    cfg = new_cfg
                    last_config = cfg.copy()
                    state["pair"] = cfg["pair"]
                    state["dry_run"] = cfg["dry_run"]
                
                ticker = client.get_ticker(cfg["pair"])
                # ticker example fields: 'ask', 'bid', 'last_trade'
                last_trade = Decimal(ticker.get("last_trade", ticker.get("ask") or ticker.get("bid") or "0"))
                last_price = float(last_trade)
                prices.append(last_price)
                LOGGER.info("%s last_trade=%s (buffer %s)", cfg["pair"], last_trade, len(prices))

                # Update state for dashboard
                state["last_price"] = last_price
                state["prices"] = list(prices)
                state["last_update"] = datetime.now().isoformat()
                write_state("bot_state.json", state)

                # First try: user-defined static targets (backwards compatible)
                executed = False
                if cfg["buy_target"] > 0 and last_trade <= cfg["buy_target"]:
                    LOGGER.info("Static rule met: BUY %s @ %s", cfg["volume"], last_trade)
                    resp = retry_with_backoff(client.place_order, retries=3, base_delay=1, pair=cfg["pair"], side="buy", volume=float(cfg["volume"]), price=float(last_trade))
                    append_trade_log(cfg["log_csv"], [time.time(), cfg["pair"], "buy", str(last_trade), str(cfg["volume"]), str(resp)])
                    executed = True

                elif cfg["sell_target"] > 0 and last_trade >= cfg["sell_target"]:
                    LOGGER.info("Static rule met: SELL %s @ %s", cfg["volume"], last_trade)
                    resp = retry_with_backoff(client.place_order, retries=3, base_delay=1, pair=cfg["pair"], side="sell", volume=float(cfg["volume"]), price=float(last_trade))
                    append_trade_log(cfg["log_csv"], [time.time(), cfg["pair"], "sell", str(last_trade), str(cfg["volume"]), str(resp)])
                    executed = True

                # If static rules didn't trigger, evaluate EMA strategy when we have enough samples
                if not executed and len(prices) >= ema_period:
                    sig = strategy.signal_from_prices(list(prices), period=ema_period)
                    LOGGER.info("Strategy signal: %s (last=%s ema_period=%s)", sig, last_price, ema_period)
                    if sig == "buy":
                        resp = retry_with_backoff(client.place_order, retries=3, base_delay=1, pair=cfg["pair"], side="buy", volume=float(cfg["volume"]), price=last_price)
                        append_trade_log(cfg["log_csv"], [time.time(), cfg["pair"], "buy_ema", str(last_price), str(cfg["volume"]), str(resp)])
                    elif sig == "sell":
                        resp = retry_with_backoff(client.place_order, retries=3, base_delay=1, pair=cfg["pair"], side="sell", volume=float(cfg["volume"]), price=last_price)
                        append_trade_log(cfg["log_csv"], [time.time(), cfg["pair"], "sell_ema", str(last_price), str(cfg["volume"]), str(resp)])

            except Exception as e:
                LOGGER.exception("Error in loop: %s", e)

            if args.once:
                break

            time.sleep(cfg["interval"])

    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user")


if __name__ == "__main__":
    main()
