from dotenv import load_dotenv
import os
from luno_client import LunoClient

load_dotenv()
api_key = os.getenv('LUNO_API_KEY')
api_secret = os.getenv('LUNO_API_SECRET')

client = LunoClient(api_key, api_secret, dry_run=False)
pair = os.getenv('PAIR','XBTNGN')
# Fetch ticker to set a safe price
try:
    t = client.get_ticker(pair)
    price = float(t.get('ask') or t.get('last_trade') or t.get('bid'))
    print('Ticker ask:', price)
except Exception as e:
    print('Ticker error', e)
    price = 1.0

# small buy test
volume = 0.00001
print('Placing test buy', volume, 'at', price)
try:
    resp = client.place_order(pair, 'buy', volume, price)
    print('Response:', resp)
except Exception as e:
    print('Order error:', e)
