# TradingView Webhook Integration Guide

## Overview

Your Luno trading bot now has a webhook endpoint that accepts **automated trading signals from TradingView**. When TradingView detects a signal you configure, it sends an alert to your bot, which automatically places buy/sell orders on Luno.

**Workflow:**
```
TradingView Alert → Your Webhook (/tv-webhook) → Luno API → Order Placed
```

---

## ✅ What's Included

### Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/tv-webhook` | POST | Receive trading signals (BUY/SELL) |
| `/tv-webhook/status` | GET | Health check - verify webhook is running |

### Features

✅ **BUY Signal Handler** - Places limit buy orders  
✅ **SELL Signal Handler** - Places limit sell orders  
✅ **Smart Pricing** - Buys 1% below market, sells 1% above (optimal execution)  
✅ **Logging** - All alerts saved to `tradingview_alerts.log`  
✅ **Error Handling** - Friendly error messages for API failures  
✅ **Validation** - Checks signal, pair, volume, credentials  
✅ **Dry-Run Support** - Safe testing without real trades  

---

## 🚀 Getting Started

### Step 1: Start the Dashboard/Webhook Server

```bash
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

**Output:**
```
Dashboard running at http://localhost:5000
...
Incoming request: GET /tv-webhook/status from 127.0.0.1
127.0.0.1 - - [16/Nov/2025 10:45:00] "GET /tv-webhook/status HTTP/1.1" 200 -
```

### Step 2: Verify Webhook is Running

Check health status:
```bash
curl http://localhost:5000/tv-webhook/status
```

**Expected Response:**
```json
{
  "status": "healthy",
  "webhook_endpoint": "/tv-webhook",
  "credentials_configured": true,
  "luno_api_status": "ok",
  "timestamp": "2025-11-16T10:45:00.123456"
}
```

---

## 📡 TradingView Alert Configuration

### 1. Create a TradingView Alert

**In TradingView Editor:**

1. Go to your chart
2. Click **Alert** → **Create Alert**
3. Choose your strategy/indicator that generates BUY/SELL signals
4. Under **Notification settings**, select **Webhook URL**
5. **Webhook URL:** Enter your public endpoint:

```
http://YOUR_PUBLIC_IP:5000/tv-webhook
```

**⚠️ IMPORTANT: To make webhook public**

Your bot is currently at `http://localhost:5000` (local only). To accept TradingView alerts from the internet, you need:

**Option A: Use ngrok (Recommended for Testing)**
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5000

# You'll get:
# Forwarding    https://abc123.ngrok.io -> http://localhost:5000
```

Then use `https://abc123.ngrok.io/tv-webhook` in TradingView.

**Option B: Deploy to VPS/Cloud**
- Set up on a cloud server (AWS, DigitalOcean, Linode, etc.)
- Use your server's public IP: `http://YOUR_SERVER_IP:5000/tv-webhook`

**Option C: Use Reverse Proxy/Port Forwarding**
- Configure your router to forward port 5000 to your machine
- Use your ISP's public IP with port forwarding

---

### 2. Configure Alert Message (JSON Format)

In TradingView **Alert Message** field, enter:

```json
{
  "signal": "{{strategy.order.action}}",
  "pair": "XBTNGN",
  "volume": 0.001
}
```

**TradingView Variables:**
- `{{strategy.order.action}}` = `"buy"` or `"sell"` (from your strategy)
- `pair` = Your Luno trading pair (e.g., `XBTNGN`, `ETHNGN`)
- `volume` = Order amount in crypto (e.g., `0.001` BTC)

**Example Alert Messages:**

**For BUY Signal:**
```json
{
  "signal": "buy",
  "pair": "XBTNGN",
  "volume": 0.001
}
```

**For SELL Signal:**
```json
{
  "signal": "sell",
  "pair": "XBTNGN",
  "volume": 0.001
}
```

---

## 🧪 Testing the Webhook

### Test 1: Manual BUY Signal

```bash
curl -X POST http://localhost:5000/tv-webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "buy", "pair": "XBTNGN", "volume": 0.001}'
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "✅ BUY order placed successfully | OrderID: 123456 | Pair: XBTNGN | Volume: 0.001 | Price: 123456.78",
  "pair": "XBTNGN",
  "signal": "buy",
  "order_id": "123456",
  "volume": 0.001,
  "price": 123456.78
}
```

### Test 2: Manual SELL Signal

```bash
curl -X POST http://localhost:5000/tv-webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "sell", "pair": "XBTNGN", "volume": 0.001}'
```

### Test 3: Invalid Signal

```bash
curl -X POST http://localhost:5000/tv-webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "hold", "pair": "XBTNGN"}'
```

**Expected Response (400 error):**
```json
{
  "status": "error",
  "message": "❌ Invalid signal: 'hold'. Must be 'buy' or 'sell'."
}
```

---

## 📊 Webhook Request/Response Format

### Request (from TradingView)

```json
POST /tv-webhook HTTP/1.1
Content-Type: application/json

{
  "signal": "buy" | "sell",
  "pair": "XBTNGN",
  "volume": 0.001  (optional - defaults to VOLUME from .env)
}
```

### Response (from Your Bot)

**Success (HTTP 200):**
```json
{
  "status": "ok",
  "message": "✅ BUY order placed successfully...",
  "pair": "XBTNGN",
  "signal": "buy",
  "order_id": "order_123456",
  "volume": 0.001,
  "price": 123456.78
}
```

**Error (HTTP 400/500):**
```json
{
  "status": "error",
  "message": "❌ Error description here",
  "pair": "XBTNGN",
  "signal": "buy",
  "error": "Full error details"
}
```

---

## 📝 Webhook Fields Reference

### Required Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `signal` | string | `"buy"` or `"sell"` | Case-insensitive |
| `pair` | string | `"XBTNGN"` | Luno pair code |

### Optional Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `volume` | float | From `.env` VOLUME | Order amount in crypto |

---

## 🔒 Security & Safety

### ✅ Best Practices

1. **Use HTTPS in Production**
   - Never expose webhook over plain HTTP on internet
   - Use SSL/TLS certificates (Let's Encrypt, etc.)

2. **Validate API Credentials**
   - Ensure `LUNO_API_KEY` and `LUNO_API_SECRET` in `.env` have **limited permissions**
   - Only enable: "View Account", "Place Orders", "Cancel Orders"
   - Disable: "Withdraw", "Transfer", etc.

3. **Start with Dry-Run Mode**
   - In `.env`, set `DRY_RUN=true` before going live
   - Webhook will place orders but not execute them
   - Review order details in logs before enabling real trades

4. **Monitor Alert Log**
   - Check `tradingview_alerts.log` frequently
   - Verify every order matches your strategy intention
   - If unexpected orders appear, disable webhook immediately

5. **Rate Limiting**
   - Luno API has rate limits (check their docs)
   - Don't create alerts that fire more than once per minute
   - Space out multiple signals across different pairs

6. **Backup DNS/Network**
   - Keep ProtonVPN active (ISP blocks api.luno.com)
   - Monitor connection status
   - Have fallback VPN ready

---

## 📋 Configuration

### Update `.env` to Control Default Behavior

```env
# Default order volume for webhook signals (if not specified in alert)
VOLUME=0.001

# Trading pair for alerts (if not specified in alert)
TRADING_PAIR=XBTNGN

# Luno API credentials (required for webhook to work)
LUNO_API_KEY=your_key_here
LUNO_API_SECRET=your_secret_here

# Safety: Set to true for testing, false for real trades
DRY_RUN=false
```

---

## 📊 Monitoring & Logs

### Alert Log File: `tradingview_alerts.log`

Every webhook alert is logged with:
- **Timestamp** - When alert was received
- **Signal** - BUY or SELL
- **Pair** - Trading pair (XBTNGN, etc.)
- **Status** - SUCCESS or FAILED
- **Details** - Order ID, volume, price, error

**Example Log:**
```
[2025-11-16 10:45:23] SIGNAL=BUY | PAIR=XBTNGN | STATUS=SUCCESS | OrderID=123456, Volume=0.001, Price=123456.78
[2025-11-16 10:46:15] SIGNAL=SELL | PAIR=XBTNGN | STATUS=SUCCESS | OrderID=123457, Volume=0.001, Price=125000.00
[2025-11-16 10:47:02] SIGNAL=BUY | PAIR=XBTNGN | STATUS=FAILED | Account has insufficient funds
```

### View Live Logs

```bash
# Watch logs in real-time (Windows PowerShell)
Get-Content tradingview_alerts.log -Tail 20 -Wait

# Or use Python
python -c "import os; os.system('type tradingview_alerts.log')"
```

---

## 🐛 Troubleshooting

### Problem: "❌ Failed to fetch status"

**Cause:** Webhook server not running  
**Solution:**
```bash
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

### Problem: "❌ Luno API credentials not configured"

**Cause:** Missing `.env` file or empty API keys  
**Solution:**
```bash
# Check .env exists and has:
cat .env
```
Must show:
```
LUNO_API_KEY=f26pmrxdbeg7m
LUNO_API_SECRET=AnRfxEGGmeu9PRGBsXgrd6Dv_Tj-rtKjtZjVBQRwCP8
```

### Problem: "❌ Invalid signal: 'hold'"

**Cause:** TradingView alert message has wrong signal value  
**Solution:** Verify TradingView alert uses `"buy"` or `"sell"` only

### Problem: "❌ Account has insufficient funds"

**Cause:** Your Luno account doesn't have enough balance  
**Solution:**
- Add more funds to Luno account, OR
- Reduce `VOLUME` in `.env` or alert message

### Problem: "❌ Network error posting order"

**Cause:** ProtonVPN disconnected or ISP blocking api.luno.com  
**Solution:**
```bash
# Verify VPN connection
# Connect to ProtonVPN again
# Test ping: ping api.luno.com
```

### Problem: TradingView says "Webhook failed"

**Cause:** Webhook URL not accessible from internet  
**Solution:**
- Use ngrok for testing: `ngrok http 5000`
- Or deploy to cloud/VPS with public IP
- Or configure port forwarding on router

---

## 🔄 Workflow Example

### Scenario: RSI Overbought/Oversold Strategy

1. **TradingView Strategy:** Detects RSI < 30 (oversold) → sends BUY alert
2. **Alert Message:**
   ```json
   {"signal": "buy", "pair": "XBTNGN", "volume": 0.001}
   ```
3. **Webhook Receives:** POST `/tv-webhook` with above data
4. **Bot Action:** 
   - Validates credentials ✅
   - Gets current BTC/NGN price: 138,088,063
   - Sets buy price 1% below: 136,707,182
   - Places limit BUY order: 0.001 BTC @ 136,707,182 NGN
5. **Response:** Returns order ID and confirmation
6. **Log Entry:** 
   ```
   [2025-11-16 10:45:23] SIGNAL=BUY | PAIR=XBTNGN | STATUS=SUCCESS | OrderID=123456, Volume=0.001, Price=136707182
   ```

---

## 📞 Support

If webhook fails:

1. Check `tradingview_alerts.log` for error details
2. Verify `.env` credentials are correct
3. Test manually: `curl http://localhost:5000/tv-webhook/status`
4. Ensure ProtonVPN is connected (if needed)
5. Review error logs in terminal output

---

## ✨ Next Steps

1. ✅ Webhook server is installed
2. ⏳ Configure ngrok for public URL (or deploy to cloud)
3. ⏳ Create TradingView alert with webhook URL
4. ⏳ Test with manual curl requests
5. ⏳ Enable in TradingView (start with paper trading)
6. ⏳ Monitor logs for 24+ hours
7. ⏳ Go live when confident

**Happy automated trading! 🚀**
