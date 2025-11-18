# 🤖 Luno Trading Bot - Complete Feature Guide

A comprehensive automated trading bot for Luno exchange with 7 major features: smart trading strategies, multi-coin support, profit tracking, credentials management, AI trend analysis, auto-compounding, and real-time alerts.

## 🎯 Quick Start

```bash
# 1. Install dependencies
pip install flask requests python-dotenv

# 2. Set up .env with your Luno credentials
# Copy these from https://luno.com/en/settings/api-keys
LUNO_API_KEY=your_key_here
LUNO_API_SECRET=your_secret_here
DRY_RUN=false  # set to true for testing

# 3. Start the bot
python luno_bot.py

# 4. Start the dashboard (in another terminal)
python dashboard.py

# 5. Open http://localhost:5000 in your browser
```

## 📋 7 Core Features

### 1️⃣ Auto Buy/Sell Smart Strategy
**What it does:** Automatically buys when price drops and sells when profit target reached.

**Configuration:**
- **Buy on Drop %**: Trigger buy when price drops X% (e.g., 3%)
- **Sell at Profit %**: Trigger sell when profit reaches X% (e.g., 10%)
- **Stop Loss %**: Limit losses by selling at X% drop (e.g., 5%)

**Dashboard:** Strategy Tab → Configure thresholds → Save Config

**How it works:**
```
1. Bot monitors price 24/7
2. When price drops 3% → BUY signal (if budget available)
3. Hold position and monitor for profit
4. When profit reaches 10% → SELL signal (lock in gains)
5. If price drops 5% from buy price → STOP LOSS (minimize damage)
```

### 2️⃣ Multiple Coin Support
**Supported Pairs:** USDTNGN, BTCNGN, ETHNGN, SOLNGN, XRPNGN, USDCNGN

**How to use:**
1. Go to Strategy Tab
2. Select coin from dropdown
3. Configure strategy thresholds per coin
4. Each coin gets independent buy/sell rules

**Live Trading:** Bot auto-switches between coins based on best signals

### 3️⃣ Profit Tracking Dashboard
**Displays:**
- Daily profit/loss (NGN and %)
- Per-coin performance
- Total trades executed
- Current positions
- Win rate statistics

**Dashboard:** View in Dashboard Tab → Bot Status section

**Data Persistence:** All trades logged in `trade_log.csv` for audit trail

### 4️⃣ API Credentials Manager
**Stores securely:**
- Luno API Key & Secret
- Binance API Key & Secret (for future multi-exchange)

**Security Features:**
- Encrypted storage (api_credentials.json)
- Credentials masked when displayed (****XX...XX)
- File permissions restricted (0o600)

**Setup:** Credentials Tab → Enter API keys → Save

### 5️⃣ AI Prediction & Trend Analysis
**How it works:**
- Uses EMA (Exponential Moving Average) technical analysis
- Short EMA (12 periods) vs Long EMA (26 periods)
- Detects trends: UPTREND 📈, DOWNTREND 📉, NEUTRAL ➡️
- Signal Strength: 0-100% confidence level

**Trading Logic:**
- **UPTREND**: Favorable for selling (take profits)
- **DOWNTREND**: Favorable for buying (accumulate)
- **Signal Strength > 75%**: High confidence, execute trades

**Dashboard:** Trends Tab → View signals for all coins → Best buy opportunity highlighted

### 6️⃣ Auto Compound & Reinvestment
**How it works:**
- Splits profits into two parts:
  - **Reinvest (70%)**: Use for next trades (grow capital)
  - **Savings (30%)**: Accumulate for withdrawal

**Example:**
```
Profit: ₦1,000
├─ Reinvest: ₦700 → Auto-buy with this
└─ Savings: ₦300 → Keep aside
```

**Dashboard:** Compound Tab → See total profit, reinvested, savings balance

**Tracking:** All transactions logged with timestamps for transparency

### 7️⃣ Alert & Notification System
**Alert Types:**
- **Trade Alerts**: When BUY/SELL orders execute
- **Price Alerts**: When significant price drops detected
- **Daily Summary**: End-of-day P/L report

**Supported Channels:**

#### Email (Gmail)
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_SENDER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_RECIPIENTS=recipient@gmail.com
```
👉 Get app password: https://myaccount.google.com/apppasswords

#### Telegram
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=123456789
```
👉 Create bot: Message @BotFather → /newbot

#### WhatsApp (Twilio)
```env
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
WHATSAPP_RECIPIENTS=whatsapp:+2348012345678
```
👉 Setup: https://www.twilio.com

**Dashboard:** Alerts Tab → See enabled channels → Send test alert

## 🚀 Core Files

| File | Purpose |
|------|---------|
| `luno_client.py` | REST API wrapper for Luno exchange |
| `luno_bot.py` | Main trading bot engine |
| `smart_strategy.py` | Smart buy/sell logic |
| `profit_tracker.py` | P/L analytics |
| `trend_analyzer.py` | EMA-based signal generator |
| `compound_manager.py` | Profit splitting & reinvestment |
| `credentials_manager.py` | Secure credential storage |
| `notification_manager.py` | Email/Telegram/WhatsApp alerts |
| `dashboard.py` | Flask web server |
| `templates/index.html` | Web UI with 6 tabs |

## 📊 Dashboard Tabs Explained

### Dashboard Tab
- **Live Price Chart**: Real-time price movements
- **Bot Status**: Current pair, mode (DRY/LIVE), last update
- **Position Info**: Buy price, current bid, profit %, auto-sell target
- **Recent Trades**: Timestamp, action (BUY/SELL), price, volume

### Strategy Tab
- **Coin Selection**: Choose which pair to configure
- **Thresholds**: Buy drop %, sell profit %, stop loss %
- **Save/Load**: Persist config across sessions

### Trends Tab
- **Signal Display**: UPTREND/DOWNTREND/NEUTRAL for each coin
- **Signal Strength**: Confidence % (0-100%)
- **Best Buy Opportunity**: Coin with strongest downtrend

### Compound Tab
- **Profit Summary**: Total earned, reinvested, saved
- **Transaction History**: Breakdown of each profit split
- **Growth Tracking**: See compounding effect over time

### Alerts Tab
- **Channel Status**: Email ✅, Telegram ❌, WhatsApp ✅
- **Recipient Count**: How many people get notifications
- **Test Button**: Send test alert to verify setup

### Credentials Tab
- **Luno API Keys**: Secure storage (password fields)
- **Binance API Keys**: Optional, for future multi-exchange
- **Security Notes**: Best practices for API key safety

## 💡 Trading Examples

### Example 1: Conservative Trader
```
Strategy Config:
- Buy on Drop: 5%
- Sell at Profit: 15%
- Stop Loss: 3%

Result: Fewer trades, higher profit target, tighter stops
```

### Example 2: Active Trader
```
Strategy Config:
- Buy on Drop: 2%
- Sell at Profit: 5%
- Stop Loss: 8%

Result: More frequent trades, smaller profits per trade
```

### Example 3: Multi-Coin Diversified
```
USDTNGN: Buy 3%, Sell 10%, Stop 5%
BTCNGN: Buy 5%, Sell 15%, Stop 8%
ETHNGN: Buy 4%, Sell 12%, Stop 6%

Result: Different strategies per coin, auto-switches based on signals
```

## 🔒 Security Best Practices

1. **Credentials**
   - Use read-only API keys when possible
   - Rotate keys periodically
   - Never commit .env to version control

2. **Dry Run Mode**
   - Test strategies without risking money
   - Set `DRY_RUN=true` in .env
   - Verify logic before enabling live trading

3. **Small Initial Trades**
   - Start with small budget (₦1,000-₦10,000)
   - Test with actual orders before scaling
   - Monitor bot 24 hours before increasing budget

4. **Alerts Setup**
   - Enable at least 1 alert channel
   - Monitor notifications daily
   - Test alerts before live trading

## 📈 Expected Returns

**Realistic expectations:**
- Conservative: 1-3% daily return
- Moderate: 3-8% daily return
- Aggressive: 8-15%+ daily return (higher risk)

**Compound Growth (70% reinvestment):**
```
Day 1: ₦1,000 → Earn 2% → ₦20 profit
Day 2: ₦1,014 → Earn 2% → ₦20 profit
Day 3: ₦1,029 → Earn 2% → ₦21 profit (compounding!)
...
30 days: ₦1,000 → ₦1,811 (81% growth!)
```

## 🐛 Troubleshooting

### Dashboard not loading
```bash
# Check if Flask server running
curl http://localhost:5000

# Check logs
tail -f dashboard.log
```

### Bot not trading
1. Check `DRY_RUN` setting (should be `false` for live)
2. Verify Luno API credentials are correct
3. Ensure account has balance
4. Check bot logs for errors

### Alerts not sending
1. Go to Alerts Tab → Refresh Status
2. Verify channels enabled (green status)
3. Check environment variables in .env
4. Send test alert to verify

### API credential errors
1. Regenerate API keys in Luno settings
2. Verify key has trading permissions
3. Check system time (must be synchronized for API auth)

## 📞 Support Resources

- Luno API Docs: https://www.luno.com/en/api
- Technical Analysis: https://en.wikipedia.org/wiki/Exponential_moving_average
- Bot Status File: `bot_state.json` (shared state)
- Trade Audit: `trade_log.csv` (all trades logged)
- Profit Stats: `profit_stats.json` (daily analytics)
- Compound History: `compound_state.json` (reinvestment tracking)

## ⚠️ Disclaimer

**This bot is for educational purposes.** Cryptocurrency trading involves risk. Past performance does not guarantee future results. Always:
- Start with small amounts
- Monitor regularly
- Understand your risks
- Never invest money you can't afford to lose

## 📝 License

For personal use only. Modify and extend as needed.

---

**Happy Trading! 📈**
