from dotenv import load_dotenv
import os, sys, traceback
load_dotenv()
from luno_client import LunoClient

api_key = os.getenv('LUNO_API_KEY')
api_secret = os.getenv('LUNO_API_SECRET')
if not api_key or not api_secret:
    print('Missing LUNO_API_KEY or LUNO_API_SECRET in environment/.env')
    sys.exit(2)

client = LunoClient(api_key, api_secret, dry_run=False)
pair = 'USDTNGN'

try:
    tick = client.get_ticker(pair)
    price = float(tick.get('ask') or tick.get('last_trade') or tick.get('bid') or 1)
    print('Ticker ask:', price)
except Exception as e:
    print('Failed to fetch ticker, aborting')
    traceback.print_exc()
    sys.exit(3)

volume = 0.001
print(f'Placing LIVE buy order: {pair} volume={volume} price={price}')
try:
    resp = client.place_order(pair, 'buy', volume, price)
    print('Order response:', resp)
except Exception as e:
    print('Order raised exception:')
    traceback.print_exc()
    # If the error is a ValueError with a dict message, print it more clearly
    try:
        if isinstance(e, ValueError) and isinstance(e.args[0], dict):
            print('Structured error:', e.args[0])
    except Exception:
        pass
    sys.exit(1)

print('Done')
