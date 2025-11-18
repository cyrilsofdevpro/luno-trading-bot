# Implementation Summary: Auto-Sell Monitor & Service Enhancements

This document summarizes all 4 major features added to the Luno Trading Bot dashboard:
1. ✅ Watchdog thread for auto-sell monitor auto-restart
2. ✅ UI controls for managing auto-sell (pair, target %, start/stop)
3. ✅ Minimum-order-size validation with friendly error messages
4. ✅ Windows service installation instructions (WINDOWS_SERVICE_SETUP.md)

---

## 1. Watchdog Thread for Auto-Sell Monitor Auto-Restart

### What's Implemented

**File:** `dashboard.py`

Added a daemon background thread that continuously monitors the auto-sell monitor subprocess:

- **Frequency:** Checks every 10 seconds if the monitor is still alive
- **Recovery:** If the monitor exits/crashes, automatically restarts it using `.env` config
- **Logging:** All actions logged to `autosell_debug.log` for debugging
- **State Persistence:** Uses `auto_sell_state.json` to track PID and status

### Key Functions

```python
def _start_auto_sell_process(pair: str = None, target_pct: float = 2.0):
    """Helper to start auto_sell_monitor.py and persist state/.env"""
    # Writes to .env, starts subprocess, updates auto_sell_state.json

def auto_sell_watchdog_loop():
    """Background watchdog that restarts monitor if it exits"""
    while True:
        status = get_auto_sell_status()
        running = status.get('running') and is_process_alive(status.get('pid'))
        if not running:
            # Restart using PAIR and target from .env
        time.sleep(10)

def start_watchdog_thread():
    """Spawn daemon thread to run watchdog_loop"""
    t = threading.Thread(target=auto_sell_watchdog_loop, daemon=True)
    t.start()
```

### How It Works

1. **Dashboard startup** → calls `start_auto_sell_on_startup()` → starts monitor
2. **Watchdog thread starts** → checks monitor status every 10 seconds
3. **If monitor crashes** → watchdog detects it via `auto_sell_state.json` and `psutil`
4. **Auto-restart** → watchdog calls `_start_auto_sell_process()` with original pair/target settings
5. **Logging** → all actions written to `autosell_debug.log`

### Testing

Verify the watchdog is running:
```powershell
Get-Content autosell_debug.log -Tail 20
# Should see messages like: "[WATCHDOG] started auto_sell_monitor PID=12345 ..."
```

---

## 2. UI Controls for Auto-Sell Management

### What's Implemented

**File:** `templates/index.html` (Dashboard UI)

Enhanced the Auto-Sell Monitor card in the Dashboard tab with new controls:

#### New Form Inputs
- **Trading Pair Dropdown:** Select which pair to monitor (USDTNGN, USDCNGN, XBTNGN, ETHNGN)
- **Target Profit %:** Already existed, now synced with server-side settings

#### Enhanced Behavior
- **Start/Stop Button:** Toggles the monitor state
- **Status Badge:** Shows RUNNING/STOPPED with visual indicators
- **Live Monitor Display:** Shows current pair, profit %, and bid price
- **Message Box:** Displays success/error feedback on actions

### JavaScript Functions

```javascript
function startAutoSell():
    // Read target % and pair from UI
    // POST /api/autosell/start { target_pct, pair }
    // Update UI to show RUNNING status
    // Start polling updateAutoSellStatus() every 3 seconds

function stopAutoSell():
    // POST /api/autosell/stop
    // Update UI to show STOPPED status
    // Stop polling interval

function updateAutoSellStatus():
    // GET /api/autosell/status
    // Update pair display and profit metrics
    // Sync pair dropdown with actual running config
```

### How to Use

1. Open dashboard → "Dashboard" tab
2. Find "Auto-Sell Monitor" card
3. Select desired trading pair from dropdown (e.g., USDTNGN)
4. Set "Target Profit %" (default 2.0)
5. Click " Start" button
6. Status badge changes to " RUNNING" with green background
7. Live Monitor box shows current pair and profit %
8. Click " Stop" to pause monitoring

### Persistence

When you start the monitor:
- Settings saved to `.env` (PAIR, AUTO_SELL_TARGET_PCT)
- PID and status saved to `auto_sell_state.json`
- Watchdog uses these values if monitor crashes and restarts

---

## 3. Minimum-Order-Size Validation

### What's Implemented

**File:** `dashboard.py`

Added validation to prevent trades below exchange minimums, which eliminates HTTP 400 errors from Luno.

#### Configuration

```python
MIN_ORDER_VOLUME = {
    'USDTNGN': 1.0,      # Minimum 1 USDT
    'USDCNGN': 1.0,      # Minimum 1 USDC
    'XBTNGN': 0.0001,    # Minimum 0.0001 BTC
    'ETHNGN': 0.001,     # Minimum 0.001 ETH
    'SOLNGN': 0.01,      # Minimum 0.01 SOL
}
```

#### Validation Points

**1. Manual Trades** (`/api/trade/place`)
```python
min_vol = get_min_volume_for_pair(pair)
if volume < min_vol:
    return jsonify({
        'success': False,
        'error': 'volume_too_small',
        'message': f'Volume {volume} is below minimum for {pair} ({min_vol}). 
                    Consider increasing the amount or consolidating balances.'
    }), 400
```

**2. Auto-Sell Immediate Sell** (`/api/autosell/sell-now`)
```python
if available < min_vol:
    return jsonify({
        'success': False,
        'error': 'volume_too_small',
        'message': f'Available {base_asset} ({available}) is below minimum for {pair} ({min_vol}). 
                    Consider consolidating funds or increasing balance before selling.'
    }), 400
```

### Error Response Example

When attempting to trade below minimum:
```json
{
    "success": false,
    "error": "volume_too_small",
    "message": "Volume 0.1 is below minimum for USDTNGN (1.0). Consider increasing the amount or consolidating balances."
}
```

### Benefits

- **Prevents exchange rejections:** No more HTTP 400 errors from Luno API
- **Clear feedback:** Users see exactly what the minimum is and why the trade failed
- **Better UX:** Dashboard can display warning banners to guide users
- **Logging:** Failed trades logged for audit trail

### Testing

```bash
# Try to sell 0.05 USDT (below 1.0 minimum for USDTNGN)
curl -X POST http://127.0.0.1:5000/api/trade/place \
  -H "Content-Type: application/json" \
  -d '{"pair":"USDTNGN","side":"sell","volume":0.05}'

# Response:
# {"success": false, "error": "volume_too_small", "message": "..."}
```

---

## 4. Windows Service Installation Instructions

### What's Provided

**File:** `WINDOWS_SERVICE_SETUP.md`

Comprehensive 50+ line guide covering 3 installation methods for running the dashboard as a Windows Service:

#### Option 1: NSSM (Non-Sucking Service Manager) - **Recommended**
- **Pros:** Best auto-restart behavior, robust process management, easy GUI editor
- **Steps:** Download NSSM → `nssm install` → configure auto-restart → start
- **Best for:** Production deployments, mission-critical setups

#### Option 2: PowerShell `sc.exe` - Built-in, No Downloads
- **Pros:** Uses Windows built-in tools, no extra dependencies
- **Steps:** Create batch wrapper → `sc.exe create` → start service
- **Best for:** Quick deployments, minimal footprint

#### Option 3: Task Scheduler - Simplest Setup
- **Pros:** No admin registry changes, familiar UI, graphical configuration
- **Steps:** Open taskschd.msc → Create Basic Task → set trigger to "At startup"
- **Best for:** Single-user machines, non-critical deployments

### Key Features Covered

1. **Installation walkthrough** for each method with command examples
2. **Auto-restart configuration:** Restarts dashboard if it crashes
3. **Log file setup:** Captures stdout/stderr for debugging
4. **Monitoring:** Check service status, view logs, verify auto-sell is active
5. **Troubleshooting:** Common issues and solutions
6. **Security:** IP whitelist, firewall rules, dedicated service account recommendations
7. **Dashboard access:** Port 5000, firewall setup, authentication

### How to Use It

1. Open `WINDOWS_SERVICE_SETUP.md` in your favorite editor
2. Follow **"Option 1: NSSM"** (recommended):
   ```powershell
   # Download NSSM from https://nssm.cc/download
   # Extract to C:\tools\nssm
   
   nssm install LunoTradingBot "C:\path\to\python.exe" "dashboard.py"
   nssm set LunoTradingBot AppDirectory "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
   nssm set LunoTradingBot AppRestartDelay 5000
   nssm start LunoTradingBot
   ```

3. Verify it's running:
   ```powershell
   Get-Service -Name LunoTradingBot
   Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/autosell/status' -UseBasicParsing
   ```

4. Check logs:
   ```powershell
   Get-Content bot.log -Tail 50
   Get-Content autosell_debug.log -Tail 50
   ```

---

## Integration Overview

### Architecture Flow

```
Dashboard Startup (dashboard.py)
│
├─→ start_auto_sell_on_startup()
│   └─→ Read PAIR, AUTO_SELL_TARGET_PCT from .env
│   └─→ Start auto_sell_monitor.py as subprocess
│   └─→ Save PID to auto_sell_state.json
│
├─→ start_watchdog_thread()
│   └─→ Spawn daemon thread
│   └─→ Every 10 seconds: check if monitor alive
│   └─→ If dead: restart with original config
│   └─→ Log to autosell_debug.log
│
└─→ Flask routes ready:
    ├─→ /api/autosell/start (accept pair + target %)
    ├─→ /api/autosell/stop
    ├─→ /api/autosell/status
    ├─→ /api/autosell/sell-now
    ├─→ /api/trade/place (with MIN_ORDER_VOLUME check)
    └─→ UI at http://localhost:5000 with controls
```

### Flow: User Starts Auto-Sell from Dashboard

1. **User opens dashboard** → logs in
2. **Dashboard tab** → sees Auto-Sell Monitor card
3. **Selects pair (USDTNGN)** and **target (2.0%)**
4. **Clicks " Start"** button
5. **Browser calls** POST `/api/autosell/start { target_pct: 2.0, pair: 'USDTNGN' }`
6. **Backend:**
   - Checks monitor not already running
   - Writes PAIR=USDTNGN and AUTO_SELL_TARGET_PCT=2.0 to `.env`
   - Starts `auto_sell_monitor.py` as subprocess
   - Saves PID to `auto_sell_state.json`
   - Returns success JSON
7. **UI updates:**
   - Button text changes to " Stop"
   - Status badge shows " RUNNING"
   - Live Monitor box displays pair and profit %
8. **Watchdog background thread** monitors PID every 10 seconds
9. **If monitor crashes**, watchdog restarts it automatically
10. **All events logged** to `autosell_debug.log`

---

## Files Modified / Created

### Modified Files
1. **`dashboard.py`** (1833 lines)
   - Added `MIN_ORDER_VOLUME` map
   - Added `get_min_volume_for_pair()` function
   - Added `_start_auto_sell_process()` helper
   - Added `auto_sell_watchdog_loop()` background worker
   - Added `start_watchdog_thread()` spawner
   - Updated `/api/trade/place` to check min volume
   - Updated `/api/autosell/sell-now` to check min volume
   - Updated `/api/autosell/start` to accept and persist `pair` parameter
   - Added `import time` for watchdog sleep

2. **`templates/index.html`**
   - Added pair selection dropdown in Auto-Sell Monitor card
   - Updated `startAutoSell()` to read and pass pair to API
   - Updated `updateAutoSellStatus()` to sync pair dropdown

### New Files
1. **`WINDOWS_SERVICE_SETUP.md`** (comprehensive installation guide)
   - 3 installation methods (NSSM, sc, Task Scheduler)
   - Monitoring and troubleshooting sections
   - Security best practices
   - Command-line examples

---

## Quick Start Commands

### Start Dashboard with All Features
```powershell
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

### Verify Auto-Sell Monitor is Running
```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/autosell/status' -UseBasicParsing | ConvertTo-Json
```

### Check Watchdog Logs
```powershell
Get-Content autosell_debug.log -Tail 20
```

### Test Minimum Volume Validation
```powershell
# This should fail with "volume_too_small" error
curl -X POST http://127.0.0.1:5000/api/trade/place \
  -H "Content-Type: application/json" \
  -d '{"pair":"USDTNGN","side":"sell","volume":0.05}'
```

### Install as Windows Service (NSSM)
```powershell
nssm install LunoTradingBot "C:\path\to\python.exe" "dashboard.py"
nssm set LunoTradingBot AppDirectory "C:\path\to\bot"
nssm set LunoTradingBot AppRestartDelay 5000
nssm start LunoTradingBot
```

---

## Verification Checklist

- ✅ Dashboard starts without errors
- ✅ Auto-sell monitor starts and PID is logged in `auto_sell_state.json`
- ✅ Watchdog thread starts and logs to `autosell_debug.log`
- ✅ UI has pair dropdown and start/stop button in Auto-Sell Monitor card
- ✅ Starting monitor from UI persists pair/target to `.env`
- ✅ Status API returns `"running": true` and current PID
- ✅ Manual trade with volume < 1.0 USDT returns "volume_too_small" error
- ✅ Auto-sell sell-now with small balance returns friendly error
- ✅ WINDOWS_SERVICE_SETUP.md provides clear installation options

---

## Security & Production Recommendations

1. **Encrypt stored API keys:** Use `cryptography.Fernet` to encrypt per-user Luno keys in DB
2. **HTTPS/TLS:** Use nginx reverse proxy with SSL certificates for production
3. **Firewall rules:** Restrict port 5000 to localhost or internal networks only
4. **IP whitelist on Luno:** Configure IP whitelist in Luno account settings for extra protection
5. **Dedicated service account:** Run Windows service under non-admin account with minimal permissions
6. **Log rotation:** Implement log rotation to prevent unlimited growth of `bot.log` and `autosell_debug.log`
7. **Monitoring:** Set up alerts for service crashes or high error rates in logs
8. **Backup:** Regular backups of `.env`, `trade_log.csv`, and database files

---

## Support & Troubleshooting

### Common Issues

**"Service won't start"**
- Check `service_error.log` for error details
- Verify Python path: `python -c "import sys; print(sys.executable)"`
- Ensure working directory contains `dashboard.py`

**"Auto-sell monitor not running"**
- Check `auto_sell_state.json` for PID
- Verify PID exists: `Get-Process -Id <pid>`
- Check `autosell_debug.log` for startup errors
- Try manually: `python auto_sell_monitor.py`

**"Port 5000 already in use"**
- Find process: `netstat -ano | findstr :5000`
- Kill process: `taskkill /PID <pid> /F`
- Or change port in `dashboard.py`

**"Trades rejected as too small"**
- Check balance via `/api/account/balances`
- Consolidate holdings or increase funds
- Review `MIN_ORDER_VOLUME` in `dashboard.py`

---

## Next Steps

1. ✅ All 4 features implemented
2. ✅ Tested and verified working
3. ✅ Documentation provided
4. 🔮 **Future enhancements:**
   - Encryption of stored API keys
   - HMAC webhook validation
   - Dashboard UI for viewing/managing watchdog logs
   - Email/SMS alerts on monitor crash/restart
   - Performance metrics dashboard
   - Multi-strategy support (multiple coin pairs simultaneously)

---

## Support & Documentation

For detailed information on each feature:
- **Auto-sell monitor:** See `auto_sell_monitor.py` source code
- **Dashboard UI:** See `templates/index.html` and `templates/index.html` JavaScript
- **Windows Service:** See `WINDOWS_SERVICE_SETUP.md`
- **API Endpoints:** See `dashboard.py` routes starting with `@app.route('/api')`
