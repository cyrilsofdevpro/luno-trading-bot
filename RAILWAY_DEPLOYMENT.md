# Railway Deployment Guide

This bot runs continuously as a worker process on Railway. No web server is needed.

## Setup Steps

### 1. Create a Railway Project
- Go to https://railway.app
- Click "New Project"
- Select "Deploy from GitHub"
- Authorize and select the `luno-trading-bot` repository

### 2. Configure Environment Variables
In Railway's environment settings, add:

```
LUNO_API_KEY=your_luno_api_key_here
LUNO_API_SECRET=your_luno_api_secret_here
ENVIRONMENT=production
DRY_RUN=false
BOT_CYCLE_INTERVAL=60
AUTO_SELL_TARGET_PCT=2.0
PAIR=USDTNGN
```

**Important**: Do NOT commit `.env` file to GitHub. Use Railway's secret management.

### 3. Project Structure
Railway will automatically:
- Install dependencies from `requirements.txt`
- Run the bot using `python main.py` (specified in `Procfile`)
- Monitor the bot and restart if it crashes

### 4. Monitor Bot Status
- View logs in Railway dashboard under "Logs" tab
- Bot logs are written to stdout and `bot.log`
- Check "Metrics" tab for resource usage

### 5. Stopping the Bot
- Go to Railway dashboard
- Click "Pause" or "Remove" dyno to stop the bot
- To restart, click "Resume"

## How the Bot Works

### main.py Entry Point
- Loads API credentials from environment variables
- Initializes bot components (SmartStrategy, LunoClient, etc.)
- Runs an infinite loop that:
  1. Fetches market data (ticker, balances)
  2. Evaluates trading signals
  3. Executes buy/sell orders based on strategy
  4. Logs results
  5. Waits (BOT_CYCLE_INTERVAL seconds) before next cycle

### Logging
- All events logged to `bot.log` (persistent storage if configured)
- Logs also stream to Railway dashboard in real-time
- Errors are logged with stack traces for debugging

### Error Handling
- If a cycle fails, the bot logs the error and continues
- If a fatal error occurs (e.g., missing API keys), bot exits with code 1
- Railway will automatically restart the bot after 10 seconds

## Testing Locally Before Deployment

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```
LUNO_API_KEY=your_test_key
LUNO_API_SECRET=your_test_secret
DRY_RUN=true
ENVIRONMENT=development
BOT_CYCLE_INTERVAL=10
```

### 3. Run the Bot
```bash
python main.py
```

You should see:
```
2025-11-18 10:30:00 - __main__ - INFO - Luno Trading Bot - Railway Deployment
2025-11-18 10:30:00 - __main__ - INFO - Environment: development
2025-11-18 10:30:00 - __main__ - INFO - 🚀 Luno Trading Bot started - running continuously...
```

Press `Ctrl+C` to stop.

## Troubleshooting

### Bot crashes immediately
- Check logs for "Missing LUNO_API_KEY or LUNO_API_SECRET"
- Ensure environment variables are set correctly in Railway
- Try DRY_RUN=true to test without live trading

### Bot not placing orders
- Check if DRY_RUN=true (test mode)
- Verify Luno API keys have "Allow Trading" permission
- Check `bot.log` for error messages
- Verify account has sufficient balance

### High CPU or memory usage
- Increase BOT_CYCLE_INTERVAL to reduce frequency
- Check if multiple bot instances are running
- Monitor using Railway's metrics dashboard

### Logs not showing
- Railway may take a few seconds to start capturing logs
- Check the "Logs" tab in Railway dashboard
- Look for `bot.log` file in persistent storage if configured

## Production Recommendations

1. **Use a persistent volume** for logs and state files
   - Configure in Railway settings
   - Mount to `/app/data` directory

2. **Set up alerting** for bot failures
   - Use Railway's integrations (Discord, Slack, etc.)
   - Configure notifications on startup/shutdown

3. **Regular backups** of trade logs and state
   - Use Railway's backup features
   - Or connect a database (PostgreSQL, MongoDB)

4. **Monitor API rate limits**
   - Luno may have rate limits on API calls
   - Adjust BOT_CYCLE_INTERVAL if needed

5. **Use separate API keys** for production
   - Create a dedicated Luno API key for Railway
   - Restrict permissions to trading only
   - Use IP whitelisting if available

## Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] Railway project created and linked
- [ ] Environment variables set (API_KEY, API_SECRET, etc.)
- [ ] `.env` file is in `.gitignore` (never commit secrets)
- [ ] `Procfile` is configured correctly
- [ ] `requirements.txt` includes all dependencies
- [ ] Bot tested locally with DRY_RUN=true
- [ ] Bot logs are being captured
- [ ] Alerting configured for failures
- [ ] Persistent storage configured (optional but recommended)

## Support

For issues with Railway deployment:
- Check Railway documentation: https://docs.railway.app
- Review bot logs in Railway dashboard
- Test locally first before deploying
- Ensure Python version compatibility (3.8+)
