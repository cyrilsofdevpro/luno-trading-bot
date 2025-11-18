# Luno Trading Bot (Python)

This is a minimal, safe starting point for building an automated trading bot for the Luno exchange.

Main features:
- Connect to Luno REST API using API key & secret (Basic auth)
- Fetch live ticker data
- Place/cancel orders (DRY-RUN by default for safety)
- Simple rule-based example: buy below a target, sell above a target
- Logs trades to a CSV file

Quick start
1. Create a Luno API key at: https://www.luno.com/en/developers
2. Copy `.env.example` to `.env` and fill `LUNO_API_KEY` and `LUNO_API_SECRET`.
3. (Optional) Set BUY_TARGET, SELL_TARGET, PAIR, INTERVAL, DRY_RUN in `.env`.
4. Install dependencies:

   pip install -r requirements.txt

5. Run the bot (dry-run default):

   python luno_bot.py

Safety notes
- DRY_RUN is True by default. Set `DRY_RUN=false` in `.env` only when you understand the code and are ready to trade live.
- Test with small sizes and on a test environment if available.

Files
- `luno_client.py`: minimal Luno REST client wrapper
- `luno_bot.py`: main loop and trading rule example
- `.env.example`: env var examples
- `requirements.txt`: python dependencies

This project is a template—adapt logic, risk controls and error handling before using with real funds.