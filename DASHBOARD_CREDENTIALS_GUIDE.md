# 🔐 Dashboard Credentials Management Guide

## Overview

The Luno Trading Bot now has a **complete zero-downtime credential management system**:
- ✅ Input credentials via dashboard UI
- ✅ Auto-validates credentials
- ✅ Saves to `.env` file automatically  
- ✅ Bot auto-reloads within 5 seconds (no restart needed!)
- ✅ No downtime during credential switch

---

## Architecture

### 1. **User Flow**
```
Dashboard UI (Password inputs)
    ↓
Validate Button Click → /api/credentials/validate
    ↓
Valid? ✅ → /api/credentials/save (write to .env)
    ↓
credential_monitor detects .env change (SHA256 hash)
    ↓
Bot auto-reloads credentials
    ↓
LunoClient reinitialized with new API key/secret
    ↓
✅ Trading continues with new credentials
```

### 2. **System Components**

#### Dashboard UI (`templates/index.html`)
- **Location:** 🔐 API Credentials tab
- **Inputs:** 
  - Luno API Key (password field)
  - Luno API Secret (password field)
- **Actions:**
  - "💾 Save Luno Credentials" button
  - Validation before save
  - Status messages (success/error/loading)

#### Backend Endpoints (`dashboard.py`)
```python
GET  /api/credentials/get          # Get current masked credentials
POST /api/credentials/validate      # Test credentials (returns balance)
POST /api/credentials/save          # Save to .env, trigger auto-reload
```

#### Credential Monitor (`credential_monitor.py`)
- Watches `.env` file for changes
- Detects changes via SHA256 hash (not polling timestamps)
- Checks every 5 seconds (configurable)
- Auto-loads credentials when detected

#### Bot Integration (`luno_bot.py`)
- Main loop calls `get_monitor().check_for_updates()`
- Reinitializes LunoClient when credentials change
- Clears price history if trading pair changes
- **No restart required!**

---

## How It Works

### Step 1: User Enters Credentials in Dashboard

Open dashboard at `http://localhost:5000` and go to **🔐 API Credentials** tab:

```
┌─────────────────────────────────────┐
│ 🔐 API Credentials Manager          │
├─────────────────────────────────────┤
│ Luno Exchange                       │
│                                     │
│ API Key: [●●●●●●●●●●●]           │
│ API Secret: [●●●●●●●●●●●]        │
│                                     │
│ [💾 Save Luno Credentials]          │
│                                     │
│ Status: ✅ Credentials saved!      │
│ 🔄 Bot will auto-reload in 5 sec  │
└─────────────────────────────────────┘
```

### Step 2: Validation

When you click "💾 Save Luno Credentials", the frontend:
1. Gets API key and secret from input fields
2. Sends to `/api/credentials/validate` endpoint
3. Backend creates temporary LunoClient and fetches balance
4. Returns success/error message

**Validation Checks:**
- ✅ Credentials provided (not empty)
- ✅ API key format valid
- ✅ API secret format valid
- ✅ Can connect to Luno API
- ✅ API key has required permissions

### Step 3: Save to .env

If validation passes:
1. Frontend sends credentials to `/api/credentials/save`
2. Backend reads existing `.env` file
3. Updates `LUNO_API_KEY` and `LUNO_API_SECRET` variables
4. Writes back to `.env` file
5. Returns success message

**Example .env after save:**
```env
# .env
LUNO_API_KEY=your_new_api_key_here
LUNO_API_SECRET=your_new_api_secret_here
TRADING_PAIR=XBTNGN
DRY_RUN=false
```

### Step 4: Auto-Reload Detection

`credential_monitor.py` continuously monitors `.env`:
1. Every 5 seconds, computes SHA256 hash of `.env` file
2. Compares with previous hash
3. If changed:
   - Reads new credentials
   - Validates format
   - Logs change (with credential masking)
   - Sets flag for bot to reload

**Log Example:**
```
🧪 Credential Monitor Started (interval: 5s)
   File: .env
   Hash: a3f9c2e1b5d8... (initial)
   
[5s later]
🔄 Change detected!
   New API Key: f26p****eg7m
   New Pair: XBTNGN
```

### Step 5: Bot Auto-Reload

In `luno_bot.py` main loop:
```python
# Main trading loop
while True:
    try:
        # Check for credential updates
        if get_monitor().check_for_updates():
            # Credentials changed!
            new_cfg = get_monitor().get_credentials()
            
            if (new_cfg["api_key"] != last_config["api_key"] or 
                new_cfg["api_secret"] != last_config["api_secret"]):
                
                # Reinitialize client
                client = LunoClient(
                    new_cfg["api_key"],
                    new_cfg["api_secret"]
                )
                print("✅ Client reinitialized!")
                last_config = new_cfg
            
            # If pair changed, clear price history
            if new_cfg["pair"] != state.get("pair"):
                state["prices"] = []
        
        # Continue trading normally...
```

---

## Usage Examples

### Example 1: Switch Luno API Account

1. Open dashboard → **🔐 API Credentials** tab
2. Enter new Luno API key (from your second account)
3. Enter new Luno API secret
4. Click "💾 Save Luno Credentials"
5. See message: `🔄 Bot will auto-reload in 5 sec`
6. Bot switches to new account **without stopping trades**

**Timeline:**
- `0s` - Click save
- `1s` - Validation in progress
- `2s` - Credentials written to `.env`
- `5s` - Monitor detects change
- `6s` - Bot loads new credentials
- `7s` - Trading continues with new account ✅

### Example 2: Update Trading Pair

1. Edit `.env` file manually:
   ```env
   TRADING_PAIR=ETHNGN  # Changed from XBTNGN
   ```
2. Save file
3. Monitor detects change within 5 seconds
4. Bot:
   - Loads new pair `ETHNGN`
   - Clears price history (required for new pair)
   - Continues trading on new pair
5. No downtime! ✅

### Example 3: Switch from Dry-Run to Live

1. Open dashboard → **🔐 API Credentials** tab
2. Edit `.env` to set `DRY_RUN=false`
3. Monitor detects change
4. Bot reloads with live mode
5. Real trades begin! 🚀

---

## API Endpoints

### GET `/api/credentials/get`
Returns currently active credentials (masked for security).

**Response:**
```json
{
  "success": true,
  "api_key": "f26p****eg7m",
  "api_secret": "h73k****a9x2",
  "pair": "XBTNGN",
  "dry_run": false
}
```

### POST `/api/credentials/validate`
Validates credentials before saving.

**Request:**
```json
{
  "api_key": "your_full_api_key",
  "api_secret": "your_full_api_secret"
}
```

**Response (Valid):**
```json
{
  "success": true,
  "message": "Credentials valid! ✅",
  "balance": {
    "USDT": 100.50,
    "XBT": 0.001,
    "ETH": 0.05
  }
}
```

**Response (Invalid):**
```json
{
  "success": false,
  "error": "Invalid credentials: API key not found"
}
```

### POST `/api/credentials/save`
Saves validated credentials to `.env` file.

**Request:**
```json
{
  "api_key": "your_full_api_key",
  "api_secret": "your_full_api_secret",
  "pair": "XBTNGN"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credentials saved! 🔄 Bot will auto-reload within 5 seconds...",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Security Features

### 1. **Credential Masking**
- Displayed as: `f26p****eg7m`
- Real value stored in `.env` only
- Never logged in full

### 2. **File Permissions**
- `.env` file readable only by bot process
- Credentials never transmitted in logs
- Password fields in UI (hidden from screen)

### 3. **Validation Before Save**
- Credentials tested against Luno API
- Failed credentials not saved
- Only valid credentials accepted

### 4. **No Version Control**
- `.env` in `.gitignore`
- Credentials never committed to repo
- Safe for public repositories

### 5. **Hash-Based Change Detection**
- SHA256 hash of entire `.env` file
- No need to parse/understand file format
- Works even if other variables change

---

## Troubleshooting

### Problem: Dashboard not saving credentials

**Solution 1:** Check backend is running
```powershell
# Check if Flask dashboard is running
# Should see: "Dashboard running at http://localhost:5000"
python dashboard.py
```

**Solution 2:** Check `.env` file permissions
```powershell
# Make sure .env is writable
ls -la .env  # On PowerShell

# If not writable, change permissions
icacls .env /grant:r "%USERNAME%:F"
```

**Solution 3:** Check credentials input
- Ensure API key and secret are not empty
- Check for extra spaces (frontend trims them)
- Verify credentials work with curl/Postman

### Problem: Credentials not reloading

**Solution 1:** Verify credential monitor is running
- Check bot console for: `🧪 Credential Monitor Started`
- Should show file path and check interval

**Solution 2:** Check `.env` file was written
```powershell
# View .env contents
cat .env

# Should show updated credentials
```

**Solution 3:** Verify hash changed
- Monitor detects changes via hash comparison
- If hash didn't change, credentials are same

### Problem: "Invalid credentials" error

**Possible causes:**
- API key/secret has typo
- Copy-paste included extra spaces
- Credentials are for different Luno account
- Luno API has rate limiting

**Solution:**
1. Double-check credentials in Luno account settings
2. Remove extra spaces (frontend strips them)
3. Try with another Luno account
4. Wait 1 minute for rate limit to reset

---

## Monitoring the Auto-Reload

Watch the bot console to see auto-reload in action:

```
🧪 Credential Monitor Started (interval: 5s)
   File: .env
   Hash: a3f9c2e1b5d8...

[User saves credentials via dashboard]

🔄 Change detected!
   New API Key: f26p****eg7m
   New Pair: XBTNGN

✅ Credentials reloaded!
✅ Client reinitialized!
🤖 Bot continues trading with new credentials...

[5s later]
[1-5] Checking for changes... No change detected
```

---

## Configuration

### Change Auto-Reload Interval

In `luno_bot.py`, modify this line:
```python
# Current: 5 second check interval
monitor = initialize_monitor(".env", check_interval=5)

# Change to 10 seconds:
monitor = initialize_monitor(".env", check_interval=10)

# Change to 2 seconds:
monitor = initialize_monitor(".env", check_interval=2)
```

### Change File Path

In `luno_bot.py`:
```python
# Current: .env in current directory
monitor = initialize_monitor(".env", check_interval=5)

# Change to specific path:
monitor = initialize_monitor("/path/to/.env", check_interval=5)
```

---

## Summary

| Feature | Status | Time |
|---------|--------|------|
| Dashboard UI | ✅ Complete | - |
| Credential Validation | ✅ Complete | ~1 sec |
| Save to .env | ✅ Complete | ~0.1 sec |
| Monitor Detection | ✅ Complete | ~5 sec |
| Bot Auto-Reload | ✅ Complete | ~0.1 sec |
| **Total Time** | **✅ Complete** | **~6 seconds** |
| **Downtime** | **✅ None** | **0 sec** |

**Result:** Zero-downtime credential updates! 🚀

---

## Next Steps

1. ✅ Start bot: `python luno_bot.py`
2. ✅ Open dashboard: `http://localhost:5000`
3. ✅ Go to **🔐 API Credentials** tab
4. ✅ Enter your Luno API key and secret
5. ✅ Click "💾 Save Luno Credentials"
6. ✅ Watch bot console for auto-reload message
7. ✅ Trading continues with new credentials!

---

## Questions?

Check the bot console logs for detailed information:
```
✅ - Success
❌ - Error
🔄 - Change detected
🔐 - Credentials action
📋 - Information
🧪 - Testing/monitoring
```

Every action is logged with masking for security! 🔒

