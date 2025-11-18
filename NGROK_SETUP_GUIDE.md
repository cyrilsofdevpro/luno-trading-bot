# ngrok Setup Guide - TradingView Webhook

## What is ngrok?

**ngrok** creates a secure tunnel from your local machine to the internet. It gives you a public URL that forwards to your local `http://localhost:5000`.

**Why you need it:**
- TradingView can't access `localhost:5000` (it's local only)
- ngrok provides a public HTTPS URL: `https://abc123.ngrok.io`
- Perfect for testing webhooks without deploying to a server

---

## Step 1: Download ngrok

### Option A: Download Directly
1. Go to: **https://ngrok.com/download**
2. Download for Windows
3. Unzip to a folder (e.g., `C:\ngrok`)

### Option B: Use Chocolatey (if installed)
```powershell
choco install ngrok
```

---

## Step 2: Create ngrok Account & Get Auth Token

1. Go to: **https://ngrok.com**
2. Click **Sign Up** (top right)
3. Create free account with email
4. Verify email
5. Go to **Dashboard** → **Your Auth Token**
6. Copy the token (looks like: `2XyZ123...`)

---

## Step 3: Configure ngrok

Open **PowerShell** and run:

```powershell
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

Replace `YOUR_AUTH_TOKEN_HERE` with your actual token from Step 2.

**Example:**
```powershell
ngrok config add-authtoken 2XyZ123abc456def789ghi
```

---

## Step 4: Start Your Flask Server

In one PowerShell terminal, start the bot:

```powershell
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

Wait for: `Running on http://127.0.0.1:5000`

---

## Step 5: Start ngrok

**Open a NEW PowerShell terminal** and run:

```powershell
ngrok http 5000
```

You'll see output like:

```
Session Status                online
Account                       your-email@example.com
Version                       3.3.5
Region                        United States (us)
Forwarding                    https://abc123def45.ngrok.io -> http://localhost:5000
Forwarding                    http://abc123def45.ngrok.io -> http://localhost:5000

Web Interface                 http://127.0.0.1:4040
```

**✅ Copy the HTTPS URL:** `https://abc123def45.ngrok.io`

This is your public webhook URL!

---

## Step 6: Use Webhook URL in TradingView

### A. In TradingView Strategy Editor

1. Open your strategy in TradingView
2. Find the alert creation section (usually `strategy.entry()` or `strategy.close()`)
3. Click **Create Alert**
4. Under **Notification Settings** → **Webhook URL**, paste:

```
https://abc123def45.ngrok.io/tv-webhook
```

(Replace with your actual ngrok URL)

### B. Alert Message Format

In the **Message** field, enter:

```json
{
  "signal": "{{strategy.order.action}}",
  "pair": "XBTNGN",
  "volume": 0.001
}
```

**Important Notes:**
- `{{strategy.order.action}}` = TradingView variable that becomes "buy" or "sell"
- Replace `XBTNGN` with your trading pair
- Replace `0.001` with your desired volume

### C. Example for RSI Strategy

```
Alert Name: RSI Buy Signal
Message:
{
  "signal": "buy",
  "pair": "XBTNGN",
  "volume": 0.001
}
Webhook URL: https://abc123def45.ngrok.io/tv-webhook
```

---

## Step 7: Test the Connection

### Test 1: Health Check

```powershell
Invoke-RestMethod -Uri "https://abc123def45.ngrok.io/tv-webhook/status" -Method GET | ConvertTo-Json
```

**Expected response:**
```json
{
  "status": "healthy",
  "webhook_endpoint": "/tv-webhook",
  "credentials_configured": true,
  "luno_api_status": "ok",
  "timestamp": "2025-11-16T10:55:00"
}
```

### Test 2: Manual Buy Signal

```powershell
$body = @{
    signal = "buy"
    pair = "XBTNGN"
    volume = 0.001
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://abc123def45.ngrok.io/tv-webhook" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Expected response:**
```json
{
  "status": "ok",
  "message": "✅ BUY order placed successfully...",
  "order_id": "123456",
  "pair": "XBTNGN",
  "volume": 0.001,
  "price": 136707182
}
```

### Test 3: Manual SELL Signal

```powershell
$body = @{
    signal = "sell"
    pair = "XBTNGN"
    volume = 0.001
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://abc123def45.ngrok.io/tv-webhook" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

---

## Step 8: Monitor Requests in Real-Time

### ngrok Web Inspector

1. Open browser: **http://127.0.0.1:4040**
2. You'll see all requests to your webhook in real-time
3. View request/response details
4. Great for debugging!

### Terminal Logs

Your Flask terminal will show:
```
[TV-WEBHOOK] Received alert: signal=buy, pair=XBTNGN, volume=0.001
[TV-WEBHOOK] Placing BUY order...
[TV-WEBHOOK] ✅ BUY order placed successfully | OrderID: 123456
```

---

## Troubleshooting

### Problem: "Connection refused" when testing

**Cause:** Flask server not running
**Solution:**
```powershell
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

### Problem: ngrok says "Invalid auth token"

**Cause:** Token copied wrong or account not verified
**Solution:**
1. Go to https://ngrok.com/dashboard
2. Copy auth token again (carefully)
3. Run: `ngrok config add-authtoken YOUR_TOKEN`

### Problem: "Webhook URL unreachable" in TradingView

**Cause:** ngrok URL not active or wrong URL
**Solution:**
1. Verify ngrok is running and showing forwarding URL
2. Test health check first: `https://your-url/tv-webhook/status`
3. Check ngrok web inspector at `http://127.0.0.1:4040`

### Problem: Requests show 404 error

**Cause:** Wrong endpoint
**Solution:**
- Use: `https://your-url/tv-webhook` (not `/api/tv-webhook`)
- Use: `https://your-url/tv-webhook/status` for health check

### Problem: ngrok keeps disconnecting

**Cause:** Free tier has session limits
**Solution:**
1. Restart ngrok: `ngrok http 5000`
2. Update your TradingView alert with new ngrok URL
3. Consider upgrading to ngrok Pro if needed for production

---

## Terminal Setup (Quick Reference)

**Terminal 1 - Flask Server:**
```powershell
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

**Terminal 2 - ngrok Tunnel:**
```powershell
ngrok http 5000
```

**Terminal 3 - Testing (Optional):**
```powershell
# Test webhook
Invoke-RestMethod -Uri "https://YOUR_NGROK_URL/tv-webhook/status" -Method GET
```

---

## Security Tips

✅ **Do:**
- Use HTTPS only (ngrok gives you HTTPS automatically)
- Keep your ngrok auth token private
- Use the ngrok web inspector to monitor requests
- Restart ngrok if you suspect leaks

❌ **Don't:**
- Share your ngrok URL publicly
- Use ngrok URL in production longterm (deploy to server instead)
- Commit ngrok URLs to git
- Use HTTP (only HTTPS)

---

## Next Steps After Testing

### Option 1: Keep Using ngrok (Development)
- Good for testing and development
- Free tier sufficient for most cases
- Session expires periodically

### Option 2: Deploy to VPS/Cloud (Production)
- More reliable than ngrok
- Permanent URL
- Full control
- Better performance

Suggested platforms:
- **AWS EC2** - $10-20/month
- **DigitalOcean** - $5-10/month
- **Linode** - $5-10/month
- **Heroku** - Free tier available (limited)

---

## Example: Full Workflow

1. **Start Flask:**
   ```powershell
   python dashboard.py
   ```

2. **Start ngrok:**
   ```powershell
   ngrok http 5000
   ```

3. **Copy ngrok URL:**
   ```
   https://abc123def45.ngrok.io
   ```

4. **Configure TradingView Alert:**
   - Strategy: Any (RSI, MACD, etc.)
   - Alert Message:
     ```json
     {"signal": "buy", "pair": "XBTNGN", "volume": 0.001}
     ```
   - Webhook URL: `https://abc123def45.ngrok.io/tv-webhook`

5. **Test:**
   ```powershell
   # Health check
   Invoke-RestMethod -Uri "https://abc123def45.ngrok.io/tv-webhook/status" -Method GET

   # Manual signal
   $body = @{signal="buy"; pair="XBTNGN"; volume=0.001} | ConvertTo-Json
   Invoke-RestMethod -Uri "https://abc123def45.ngrok.io/tv-webhook" -Method POST -ContentType "application/json" -Body $body
   ```

6. **Monitor:**
   - Check ngrok inspector: `http://127.0.0.1:4040`
   - Check Flask logs for `[TV-WEBHOOK]` messages
   - Check `tradingview_alerts.log` file for audit trail

---

## Support

If you encounter issues:

1. Check `tradingview_alerts.log` for error details
2. View ngrok web inspector at `http://127.0.0.1:4040`
3. Check Flask terminal output for `[TV-WEBHOOK]` logs
4. Verify VPN (ProtonVPN) is connected
5. Test health endpoint: `https://your-url/tv-webhook/status`

**You're ready to connect TradingView to your bot!** 🎉

