import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
pair = 'XBTNGN'

t = requests.get('https://api.luno.com/api/1/ticker', params={'pair': pair})
ask = float(t.json()['ask'])
price = str(int(ask * 0.9))

print(f"Testing postorder for {pair}")
print(f"Price: {price}")
print()

# The working order had type='BID', so test form-encoded (not JSON)
tests = [
    ('type=BID, form data', {'pair': pair, 'type': 'BID', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}, 'form'),
    ('type=ASK, form data', {'pair': pair, 'type': 'ASK', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}, 'form'),
    ('type=bid, form data', {'pair': pair, 'type': 'bid', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}, 'form'),
    ('type=ask, form data', {'pair': pair, 'type': 'ask', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}, 'form'),
]

for name, payload, method in tests:
    try:
        if method == 'form':
            r = requests.post('https://api.luno.com/api/1/postorder', auth=(API_KEY, API_SECRET), data=payload)
        else:
            r = requests.post('https://api.luno.com/api/1/postorder', auth=(API_KEY, API_SECRET), json=payload)
        
        if r.status_code == 200:
            print(f'✓ {name}: SUCCESS!')
            data = r.json()
            print(f'  Order ID: {data.get("order_id")}')
        else:
            error_data = r.json()
            error_msg = error_data.get('error', error_data.get('error_code', str(error_data)))
            print(f'✗ {name}: HTTP {r.status_code}')
            print(f'  Error: {error_msg}')
    except Exception as e:
        print(f'✗ {name}: Exception: {e}')
