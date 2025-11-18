# ✨ AUTO-RELOAD CREDENTIALS FEATURE - QUICK START

## What This Does

Your bot now **automatically detects when you update your `.env` file** and reloads credentials **WITHOUT restarting**!

```
Old Way:
  1. Update .env ❌
  2. Kill bot process 💀
  3. Restart bot ⏱️
  4. Wait for restart ⏳
  Total: ~30 seconds downtime

New Way:
  1. Update .env ✅
  2. Bot automatically detects (within 5 seconds)
  3. Credentials reload instantly ⚡
  4. Zero downtime! 🚀
```

---

## How to Use

### Step 1: Get New API Key
- Log in to https://luno.com
- Go to Settings → API Keys
- Create new key or copy existing key

### Step 2: Update `.env` File
```bash
# Edit .env
LUNO_API_KEY=your_new_key_here
LUNO_API_SECRET=your_new_secret_here
DRY_RUN=false
```

### Step 3: Save File
Just save! That's it! The bot will automatically detect and reload.

### Step 4: Check Logs
You'll see:
```
🔄 Change detected in .env file, reloading credentials...
📝 Credentials updated:
   • api_key: f26p****7m → a1b2****xyz
🔄 API credentials changed, reinitializing client...
✅ Client reinitialized with new credentials
```

---

## Features

| Feature | Status | Time |
|---------|--------|------|
| Auto-detect .env changes | ✅ YES | ~5 seconds |
| Reload credentials | ✅ YES | Automatic |
| Reinitialize API client | ✅ YES | Automatic |
| Change logging | ✅ YES | With masking |
| Zero downtime | ✅ YES | No restart |
| Security | ✅ YES | Credentials masked |

---

## What Reloads

✅ **API Key** - New key used immediately  
✅ **API Secret** - New secret used immediately  
✅ **Trading Pair** - If changed, switches to new pair  
✅ **DRY_RUN Mode** - Can toggle live/test mode  

---

## Testing

### Test the Feature
```bash
python test_credential_reload.py
```

### Expected Output
```
🧪 Testing Credential Auto-Reload System
============================================================

1️⃣ Initial Load
✅ Credentials loaded:
  API Key: f26p****7m
  Pair: USDTNGN
  Mode: LIVE TRADING

2️⃣ Simulating .env file edit...
Monitoring for changes...
✅ Auto-reload test complete!
```

---

## Real-World Usage

### Scenario: Rotating API Key

**Timeline:**
```
10:00 - Bot running with Key A
10:05 - You update .env with Key B
10:05-10:10 - Bot automatically reloads
10:10 - Bot now using Key B, still trading!
```

**No Downtime!** ✅  
**No Missed Trades!** ✅  
**No Restarts!** ✅  

---

## Implementation

### Files Updated
- ✅ `credential_monitor.py` - New module for monitoring
- ✅ `luno_bot.py` - Integrated auto-reload logic
- ✅ `test_credential_reload.py` - Test script
- ✅ `AUTO_RELOAD_GUIDE.md` - Full documentation

### How It Works (Technical)

1. **Monitor Module** monitors `.env` file using SHA256 hash
2. **Hash Check** every 5 seconds (configurable)
3. **Change Detection** when hash changes
4. **Auto-Load** uses `load_dotenv(override=True)`
5. **Client Reinit** creates new Luno API client
6. **Log Update** shows what changed (with masking)

---

## Configuration

### Check Interval (Default: 5 seconds)
Edit `luno_bot.py` line 20:
```python
monitor = initialize_monitor(".env", check_interval=5)  # Change to 10, 30, etc.
```

**Recommendations:**
- 5 seconds ⭐ (default, fastest)
- 10 seconds (balanced)
- 30 seconds (lazy)

### Disable Auto-Reload
Set to very large number:
```python
monitor = initialize_monitor(".env", check_interval=999999)
```

---

## Security

✅ **Credentials Masked** - Logs show `****XX...XX`  
✅ **File Monitored Only** - No credentials in logs  
✅ **Restricted Permissions** - `.env` protected  
✅ **Memory Safe** - Credentials in memory only  
✅ **Change Audited** - Logs when credentials change  

---

## Troubleshooting

### Bot not detecting changes?
1. Make sure `.env` was actually saved
2. Wait 5+ seconds (check interval)
3. Check logs for "Change detected" message
4. Restart bot to force reload

### Still using old credentials?
1. Verify new credentials in `.env`
2. Check logs for reload confirmation
3. Restart bot if needed

### See Also
For more details: **`AUTO_RELOAD_GUIDE.md`**

---

## Summary

🎉 **Your bot now auto-reloads credentials!**

- No restart needed
- Changes detected in ~5 seconds
- Zero trading downtime
- Secure credential handling
- Production ready

**Update your `.env` and the bot automatically adapts! 🚀**
