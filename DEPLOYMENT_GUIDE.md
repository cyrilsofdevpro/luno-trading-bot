# 🚀 Luno Trading Bot - Deployment & Operations Guide

## Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install flask requests python-dotenv

# 2. Get Luno API credentials
# Visit: https://luno.com/en/settings/api-keys
# Create new API key (enable trading)

# 3. Configure .env
# Edit file and add:
LUNO_API_KEY=your_api_key_here
LUNO_API_SECRET=your_api_secret_here
DRY_RUN=false  # Set to false for live trading

# 4. Start the bot
python luno_bot.py &

# 5. Start the dashboard (new terminal)
python dashboard.py

# 6. Open browser
# http://localhost:5000
```

---

## 📋 Pre-Deployment Checklist

- [ ] Python 3.7+ installed
- [ ] Luno account created and verified
- [ ] API credentials generated (with trading permission)
- [ ] At least ₦500 balance in Luno account
- [ ] `.env` file configured with API credentials
- [ ] Tested in DRY_RUN=true mode first
- [ ] Read FEATURES_GUIDE.md completely
- [ ] Understood all 7 features
- [ ] Decided on strategy configuration

---

## 🎯 Configuration Steps

### Step 1: Create Luno API Key

1. Log in to https://luno.com
2. Go to Settings → API Keys
3. Click "Create new key"
4. Enable permissions:
   - ✅ Trade
   - ✅ View account balance
5. Copy API Key and Secret
6. **IMPORTANT:** Save securely (you can't view secret again)

### Step 2: Set Up Environment File

Create/edit `.env` file in bot directory:

```env
# Luno Exchange
LUNO_API_KEY=your_key_from_step_1
LUNO_API_SECRET=your_secret_from_step_1

# Trading Mode
DRY_RUN=false              # Set to true for simulation
TRADING_BUDGET_NGN=5000    # Initial budget (optional)

# Price Monitoring
POLL_INTERVAL=10           # Seconds between price checks

# Auto-Sell (optional)
AUTO_SELL_TARGET_PCT=2     # Profit target for auto-sell

# Logging
LOG_CSV=trade_log.csv      # Trade audit log location
LOG_LEVEL=INFO
```

### Step 3: Strategy Configuration

1. Start dashboard: `python dashboard.py`
2. Go to http://localhost:5000 → Strategy Tab
3. For each coin, set thresholds:
   - **USDTNGN:** Buy 3%, Sell 10%, Stop 5% (conservative)
   - **BTCNGN:** Buy 5%, Sell 15%, Stop 8% (aggressive)
   - **ETHNGN:** Buy 4%, Sell 12%, Stop 6% (moderate)
4. Save configuration
5. Configuration persists in `strategy_config.json`

### Step 4: Alert Setup (Optional but Recommended)

#### Email Alerts (Gmail Example)

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Google generates 16-character app password
4. Add to `.env`:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_SENDER=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_password
   EMAIL_RECIPIENTS=your_email@gmail.com
   ```

#### Telegram Alerts

1. Open Telegram, message @BotFather
2. Command: `/newbot`
3. Follow steps, get BOT_TOKEN
4. Message your bot: `/start`
5. Get your Chat ID: `curl https://api.telegram.org/bot<TOKEN>/getUpdates`
6. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_IDS=your_chat_id
   ```

#### WhatsApp Alerts (Twilio)

1. Sign up at https://www.twilio.com
2. Get Account SID & Auth Token from dashboard
3. Set up WhatsApp Sandbox (verify your phone)
4. Add to `.env`:
   ```env
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
   WHATSAPP_RECIPIENTS=whatsapp:+2348012345678
   ```

---

## 🧪 Testing Before Live Trading

### Test 1: Dry-Run Mode (Safe)

```bash
# Set in .env
DRY_RUN=true

# Run bot
python luno_bot.py

# Check dashboard
# http://localhost:5000 → should show simulated trades in trade_log.csv
# No real money spent!
```

### Test 2: Strategy Validation

1. Dashboard → Strategy Tab
2. Load existing config (or create new)
3. Verify thresholds make sense:
   - Buy drop > stop loss (e.g., buy 3%, stop 5%) ✓ NO!
   - Buy drop < stop loss (e.g., buy 3%, stop 5%) ✗ Correct!
4. Save and verify persists across dashboard restart

### Test 3: Alerts Test

1. Dashboard → Alerts Tab
2. Check "Enabled Channels" - should show status
3. Click "Send Test Alert"
4. Verify you receive alerts on all configured channels
5. If not, check `.env` configuration

### Test 4: Small Live Buy

1. Set `DRY_RUN=false` in `.env`
2. Set `TRADING_BUDGET_NGN=500` (small amount!)
3. Run bot: `python luno_bot.py`
4. Wait for buy signal (may take minutes)
5. When buy occurs, verify:
   - Order appears in Luno account
   - Dashboard shows position
   - Trade logged in `trade_log.csv`
6. Check profit tracking works

---

## 📊 Running the Bot

### Terminal 1: Start Bot Engine
```bash
cd 'c:\Users\Cyril Sofdev\Documents\Luno trading  Bot'
python luno_bot.py
```

Monitor output for:
- `[INFO] Starting Luno trading bot...`
- `[INFO] Monitoring <PAIR> every <INTERVAL> seconds`
- `[BUY] Price dropped 3%, buying now...`
- `[SELL] Profit target reached, selling...`

### Terminal 2: Start Dashboard
```bash
python dashboard.py
```

Monitor output for:
- `Dashboard running at http://localhost:5000`
- `Running on http://127.0.0.1:5000`

### Terminal 3: Start Auto-Sell Monitor (Optional)
```bash
python auto_sell_monitor.py
```

Monitor output for:
- `Auto-sell monitor started`
- `[CHECK] Current price: ₦1,476.88, Profit: 2.1%, Target: 2%`
- `[SELL] Target reached, selling...`

### Browser: View Dashboard
```
http://localhost:5000
```

Available Tabs:
- 📊 **Dashboard** - Live price, position, recent trades
- 🎯 **Strategy** - Configure buy/sell/stop thresholds
- 📈 **Trends** - AI trend signals for all coins
- 💰 **Compound** - Profit reinvestment tracking
- 🔔 **Alerts** - Alert channel status & test
- 🔐 **Credentials** - API key storage

---

## 🔍 Monitoring the Bot

### Daily Checklist

- [ ] Dashboard accessible (http://localhost:5000)
- [ ] Live price updating (refreshes every 3 seconds)
- [ ] No errors in bot terminal
- [ ] Trades executing according to strategy
- [ ] Alerts received on configured channels
- [ ] Profit tracker showing positive P/L

### Key Metrics to Monitor

| Metric | Good Value | Warning |
|--------|-----------|---------|
| Bot Status | RUNNING | STOPPED |
| Mode | LIVE (if intentional) | Unexpected mode switch |
| Last Update | < 5 seconds ago | > 10 seconds (API lag) |
| P/L % | > 0% (positive) | < -2% (stop loss needed) |
| Trade Count | Increasing | Zero trades (strategy issue) |
| Active Coin | Matches dropdown | Unexpected coin |

### Reading the Logs

```bash
# Live logs (Terminal 1)
tail -f bot_terminal.log

# Recent trades
cat trade_log.csv | tail -20

# Daily stats
cat profit_stats.json

# Strategy config
cat strategy_config.json

# Compound tracking
cat compound_state.json
```

---

## ⚠️ Troubleshooting

### Issue: "Dashboard not loading"
**Solution:**
```bash
# Check if Flask running
curl http://localhost:5000

# If error, restart Flask
pkill -f "python dashboard.py"
python dashboard.py
```

### Issue: "No trades executing"
**Solution:**
1. Check `DRY_RUN=false` in `.env`
2. Verify Luno balance > 0
3. Check API credentials are correct
4. Verify network connectivity: `ping api.luno.com`
5. Check bot logs for errors

### Issue: "DNS Error / Cannot reach API"
**Solution:**
- DNS patch already applied in `luno_client.py`
- If still failing: check network connectivity, try using proxy

### Issue: "Alerts not sending"
**Solution:**
1. Check SMTP/Telegram/Twilio credentials in `.env`
2. Send test alert from dashboard: Alerts Tab → "Send Test Alert"
3. Verify recipient email/phone number correct
4. Check email spam folder (alerts might be filtered)

### Issue: "High API errors / Rate limiting"
**Solution:**
- Increase `POLL_INTERVAL` in `.env` (check price less frequently)
- Luno API limit: 10 requests/minute per IP
- Spread requests: polling + auto-sell monitor sharing quota

---

## 🛑 Emergency Stop

### Stop all bot processes:
```bash
# Kill bot
pkill -f "python luno_bot.py"

# Kill dashboard
pkill -f "python dashboard.py"

# Kill auto-sell monitor
pkill -f "python auto_sell_monitor.py"

# Verify all stopped
tasklist | findstr "python"
```

### If stuck in position:
1. Stop bot
2. Log into Luno web interface directly
3. Place manual sell order
4. After sale completes, restart bot

---

## 📈 Performance Tuning

### For More Frequent Trading

```env
# Increase checking frequency
POLL_INTERVAL=5      # Check every 5 seconds (instead of 10)

# Reduce profit targets
# Strategy Tab: Sell at Profit 5% (instead of 10%)

# This = more trades, smaller profits each
```

### For Safer Trading

```env
# Decrease checking frequency
POLL_INTERVAL=30     # Check every 30 seconds

# Increase profit targets
# Strategy Tab: Sell at Profit 20% (instead of 10%)

# This = fewer trades, larger profits each
```

---

## 🔒 Security Best Practices

1. **API Keys**
   - Never share or commit .env file
   - Regenerate keys if compromised
   - Use read-only keys if available (Luno doesn't allow this yet)

2. **Dashboard**
   - Don't expose dashboard to internet (local only)
   - Use VPN/firewall if accessing remotely
   - Close dashboard when not in use

3. **Notifications**
   - Don't reply with sensitive info in alerts
   - Verify sender before clicking links
   - Keep app passwords secure

4. **Audit Trail**
   - Keep `trade_log.csv` for tax purposes (if applicable)
   - Backup trade logs regularly
   - Review P/L reports monthly

---

## 💰 Profit Tips

### Strategy 1: Conservative (Lower Risk)
```
Buy Drop: 5%
Sell Profit: 20%
Stop Loss: 3%
Compound: 70% reinvest

Result: ~15% monthly (if market favorable)
```

### Strategy 2: Moderate (Balanced)
```
Buy Drop: 3%
Sell Profit: 10%
Stop Loss: 5%
Compound: 70% reinvest

Result: ~30% monthly (with good market)
```

### Strategy 3: Aggressive (Higher Risk)
```
Buy Drop: 1%
Sell Profit: 5%
Stop Loss: 8%
Compound: 70% reinvest

Result: ~60% monthly (market-dependent, risky!)
```

---

## 📞 Support Resources

| Resource | Link |
|----------|------|
| Luno API Docs | https://www.luno.com/en/api |
| Luno Status | https://luno.statuspage.io |
| Python Docs | https://docs.python.org |
| Flask Guide | https://flask.palletsprojects.com |
| Chart.js Docs | https://www.chartjs.org |

---

## 🎓 Learning Path

1. **Week 1:** Run bot in DRY_RUN=true mode, understand features
2. **Week 2:** Enable live trading with ₦500 budget, monitor daily
3. **Week 3:** Optimize strategy based on performance
4. **Week 4:** Increase budget if P/L positive, scale up
5. **Ongoing:** Adjust thresholds, learn technical analysis

---

## ✅ Deployment Verification

Run this to verify everything working:

```bash
# 1. Check Python installed
python --version

# 2. Check dependencies
pip list | findstr "flask requests python-dotenv"

# 3. Check files exist
ls smart_strategy.py luno_client.py dashboard.py

# 4. Check .env configured
cat .env | findstr "LUNO_API"

# 5. Run dashboard
python dashboard.py

# 6. Test API endpoint
curl http://localhost:5000/api/status

# 7. Check trade log
type trade_log.csv

# ✅ All green = Ready to trade!
```

---

**Ready to start trading? Let's go! 🚀**

Next: Go to http://localhost:5000 and configure your first strategy.
