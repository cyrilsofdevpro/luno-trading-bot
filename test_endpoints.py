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

# Test different endpoint versions and parameter combinations
tests = [
    ('v1/postorder form', 'https://api.luno.com/api/1/postorder', 'form', {'pair': pair, 'side': 'BUY', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}),
    ('v1/postorder JSON', 'https://api.luno.com/api/1/postorder', 'json', {'pair': pair, 'side': 'BUY', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}),
    ('v2/postorder form', 'https://api.luno.com/api/2/postorder', 'form', {'pair': pair, 'side': 'BUY', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}),
    ('v2/postorder JSON', 'https://api.luno.com/api/2/postorder', 'json', {'pair': pair, 'side': 'BUY', 'volume': '0.0001', 'price': price, 'order_type': 'limit'}),
]

for name, url, method, payload in tests:
    try:
        if method == 'form':
            r = requests.post(url, auth=(API_KEY, API_SECRET), data=payload)
        else:
            r = requests.post(url, auth=(API_KEY, API_SECRET), json=payload)
        
        if r.status_code == 200:
            print(f'✓ {name}: HTTP 200 SUCCESS')
            print(f'  Response: {r.json()}')
        else:
            error = r.json().get('error', r.text[:100])
            print(f'✗ {name}: HTTP {r.status_code} - {error}')
    except Exception as e:
        print(f'✗ {name}: {e}')
