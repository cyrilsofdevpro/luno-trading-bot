from luno_client import LunoClient
from dotenv import load_dotenv
import os, json, requests

load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
PAIR = os.getenv('PAIR','XBTNGN')

client = LunoClient(API_KEY, API_SECRET, dry_run=False)

try:
    ticker = client.get_ticker(PAIR)
    price = float(ticker.get('ask') or ticker.get('last_trade') or ticker.get('bid'))
except Exception as e:
    print('Failed to fetch ticker:', e)
    price = 1.0

# Conservative test volume: 0.001 XBT (increase if you want larger)
volume = 0.001
print('Attempting LIVE order:', PAIR, 'BUY', volume, 'at', price)
try:
    resp = client.place_order(PAIR, 'buy', volume, price)
    print('Order response:', json.dumps(resp))
except Exception as e:
    # try to show response body if available
    resp = getattr(e, 'response', None)
    if isinstance(resp, requests.Response):
        try:
            print('ERROR JSON:', json.dumps(resp.json()))
        except Exception:
            print('ERROR TEXT:', resp.text)
    else:
        print('Exception:', str(e))
