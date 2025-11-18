import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
pair = 'XBTNGN'

t = requests.get('https://api.luno.com/api/1/ticker', params={'pair': pair})
ask = float(t.json()['ask'])
# Use a very small volume to minimize funds required
volume = '0.00001'
price = str(int(ask * 0.9))

print(f"Testing minimal postorder for {pair}")
print(f"Volume: {volume}")
print(f"Price: {price}")
print()

# Test with correct format: type=BID, form-encoded
payload = {
    'pair': pair,
    'type': 'BID',
    'volume': volume,
    'price': price,
    'order_type': 'limit'
}

print(f"Payload: {payload}")
try:
    r = requests.post('https://api.luno.com/api/1/postorder', 
                      auth=(API_KEY, API_SECRET), 
                      data=payload)
    
    print(f'HTTP {r.status_code}')
    data = r.json()
    
    if r.status_code == 200:
        print(f'✓ SUCCESS!')
        print(f'  Order ID: {data.get("order_id")}')
    else:
        print(f'✗ Error: {data.get("error", data.get("error_code"))}')
except Exception as e:
    print(f'✗ Exception: {e}')
