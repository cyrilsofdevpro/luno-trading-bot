# 🚀 Dashboard Credentials - Quick Start

## TL;DR

Your dashboard **now supports zero-downtime credential updates!**

### How to Use

1. **Start the bot:**
   ```powershell
   python luno_bot.py
   ```

2. **Open dashboard:**
   ```
   http://localhost:5000
   ```

3. **Click 🔐 API Credentials tab**

4. **Enter your Luno credentials:**
   - API Key: `your_luno_api_key`
   - API Secret: `your_luno_api_secret`

5. **Click 💾 Save Luno Credentials**

6. **Watch the magic:**
   ```
   🔍 Validating credentials...
   💾 Saving credentials...
   ✅ Credentials saved! 🔄 Bot will auto-reload within 5 seconds...
   ```

7. **Bot auto-reloads** (check console for "✅ Client reinitialized!")

8. **Trading continues** with new credentials! ✅

---

## What Happens Behind the Scenes

```
You enter credentials in dashboard
        ↓
Frontend validates them
        ↓
Credentials written to .env file
        ↓
credential_monitor detects change (every 5 seconds)
        ↓
Bot reloads credentials
        ↓
LunoClient recreated with new API key/secret
        ↓
✅ Trading continues - NO RESTART NEEDED!
```

---

## The 3 Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/credentials/get` | GET | Get current masked credentials |
| `/api/credentials/validate` | POST | Test credentials work |
| `/api/credentials/save` | POST | Save to .env + trigger reload |

---

## Flow Timeline

| Time | Action |
|------|--------|
| 0s | You click "Save" button |
| 1s | Frontend validates credentials |
| 2s | Credentials written to .env |
| 5s | Monitor detects .env change |
| 6s | Bot loads new credentials |
| 7s | Trading resumes ✅ |

**Downtime: ZERO seconds** 🎉

---

## Security

✅ Credentials masked in UI: `f26p****eg7m`
✅ Password input fields (hidden)
✅ Test validation before save
✅ .env not in version control
✅ Hashed change detection

---

## Troubleshooting

**Dashboard not responding?**
- Check Flask is running: `python dashboard.py`
- Open `http://localhost:5000` in browser

**Credentials not saving?**
- Check `.env` file is writable
- Verify credentials are correct (try in Luno account)
- Check for extra spaces in input fields

**Not auto-reloading?**
- Ensure `credential_monitor.py` is imported in bot
- Check bot console for "🧪 Credential Monitor Started"
- Verify .env file was updated

---

## Full Documentation

See `DASHBOARD_CREDENTIALS_GUIDE.md` for complete details including:
- Detailed architecture
- API endpoint documentation
- Configuration options
- Advanced troubleshooting
- Security considerations

---

## Questions?

Check the bot console! Every action logs with emojis:
- ✅ Success
- ❌ Error
- 🔄 Change detected
- 📋 Information
- 🔐 Credentials action
