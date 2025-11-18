import requests, os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
pair = 'XBTNGN'

t = requests.get('https://api.luno.com/api/1/ticker', params={'pair': pair})
ask = float(t.json()['ask'])
price = str(int(ask * 0.5))  # Lower price = lower cost
volume = '0.001'

payload = {'pair': pair, 'type': 'BID', 'volume': volume, 'price': price, 'order_type': 'limit'}
print(f'Payload: {payload}')
r = requests.post('https://api.luno.com/api/1/postorder', auth=(API_KEY, API_SECRET), data=payload)
print(f'HTTP {r.status_code}')
data = r.json()
if r.status_code == 200:
    print(f'SUCCESS! Order ID: {data.get("order_id")}')
else:
    print(f'Error: {data.get("error")}')
