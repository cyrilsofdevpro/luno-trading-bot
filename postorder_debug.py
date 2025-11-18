import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
PAIR = os.getenv('PAIR', 'XBTNGN')

url = 'https://api.luno.com/api/1/postorder'
# Small test volume and price (use current ticker to pick a safe price)
# Fetch ticker
try:
    t = requests.get('https://api.luno.com/api/1/ticker', params={'pair': PAIR})
    t.raise_for_status()
    ticker = t.json()
    price = ticker.get('ask') or ticker.get('last_trade') or ticker.get('bid')
    print('Ticker price:', price)
except Exception as e:
    print('Ticker fetch failed:', e)
    price = None

# Many Luno endpoints expect a 'side' parameter rather than 'type' and use
# values like 'ASK' (sell) and 'BID' (buy). We'll try that format here.
tests = []
# try different parameter names/values combinations
for key, val in [('side','ASK'), ('side','BID'), ('side','SELL'), ('side','sell'), ('type','ASK'), ('type','BID'), ('type','SELL'), ('type','sell'), ('order_side','ASK'), ('order_side','SELL'), ('side','1'), ('type','1')]:
    payload = {
        'pair': PAIR,
        'volume': '0.0001',
        'price': price or '1',
        'order_type': 'limit'
    }
    payload[key] = val
    tests.append(payload)

for payload in tests:
    print('\nTrying payload:', payload)
    try:
        resp = requests.post(url, auth=(API_KEY, API_SECRET), data=payload)
        print('HTTP', resp.status_code)
        try:
            print('Response JSON:', json.dumps(resp.json()))
        except Exception:
            print('Response text:', resp.text)
    except Exception as e:
        print('Request error:', e)
