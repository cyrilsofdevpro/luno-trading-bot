import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
pair = 'XBTNGN'

# Try /markets endpoint
try:
    r = requests.get('https://api.luno.com/api/1/markets', auth=(API_KEY, API_SECRET))
    print('Markets endpoint HTTP:', r.status_code)
    if r.status_code == 200:
        data = r.json()
        markets = data.get('markets', [])
        print(f'Found {len(markets)} markets')
        for m in markets[:10]:
            if m.get('pair') == pair:
                print(f">>> FOUND: {m.get('pair')}: market_id={m.get('market_id')}")
            else:
                print(f"  {m.get('pair')}: market_id={m.get('market_id')}")
    else:
        print('Response:', r.text[:200])
except Exception as e:
    print('Markets fetch error:', e)

# Now test postorder with market_id
print('\n--- Testing postorder with market_id ---')
try:
    t = requests.get('https://api.luno.com/api/1/ticker', params={'pair': pair})
    ask = float(t.json()['ask'])
    price = str(int(ask * 0.9))
    
    payload = {
        'market_id': 'XBTNGN',  # Try the pair as market_id
        'side': 'BUY',
        'volume': '0.0001',
        'price': price,
        'order_type': 'limit'
    }
    
    print(f'Posting: {payload}')
    r = requests.post('https://api.luno.com/api/1/postorder', 
                      auth=(API_KEY, API_SECRET), 
                      json=payload)
    print(f'HTTP {r.status_code}')
    print(r.json())
except Exception as e:
    print('Error:', e)
