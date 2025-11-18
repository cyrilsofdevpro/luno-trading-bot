# ALERT SETUP GUIDE FOR LUNO TRADING BOT

## Email Alerts (Gmail Example)

To enable email alerts, you need:

1. Gmail Account
2. App Password (NOT your main password):
   - Go to https://myaccount.google.com/apppasswords
   - Generate an app password for "Mail"
   - Copy the 16-character password

3. Add to .env:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_SENDER=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
EMAIL_RECIPIENTS=recipient1@gmail.com,recipient2@gmail.com
```

## Telegram Alerts

To enable Telegram alerts:

1. Create a Telegram Bot:
   - Message @BotFather on Telegram
   - Command: /newbot
   - Follow the steps, copy the BOT_TOKEN

2. Get your Chat ID:
   - Start the bot (@YourNewBotName)
   - Message it: /start
   - Run: curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   - Find your "id" in the response

3. Add to .env:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_IDS=123456789,987654321
```

## WhatsApp Alerts (Twilio)

To enable WhatsApp alerts:

1. Create Twilio Account:
   - Sign up at https://www.twilio.com
   - Get Account SID and Auth Token from dashboard

2. Configure WhatsApp Sandbox:
   - Go to Messaging > Try it Out > Send a WhatsApp Message
   - Click "Get a Sandbox Number"
   - Add your phone number to sandbox

3. Add to .env:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
WHATSAPP_RECIPIENTS=whatsapp:+2348012345678
```

## Alert Types

1. **Trade Alerts**: Sent when BUY/SELL orders are executed
2. **Price Drop Alerts**: Sent when significant price drops detected
3. **Daily Summary**: Sent daily with P/L, trade count, reinvestment stats

## Testing Alerts

Use the dashboard test endpoint:
```bash
curl -X POST http://localhost:5000/api/alerts/test
```

Check status of enabled channels:
```bash
curl http://localhost:5000/api/alerts/status
```

## Notes

- Alerts work best with at least ONE channel enabled
- Use comma-separated lists for multiple recipients
- Keep credentials secure - never commit .env to version control
- Test alerts before enabling auto-trading
