import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')

# Test 1: Get account info (requires auth)
print("=== Test 1: Get Account Info (auth test) ===")
try:
    r = requests.get('https://api.luno.com/api/1/accounts', auth=(API_KEY, API_SECRET))
    print(f'HTTP {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f"Accounts: {data}")
    else:
        print(f"Error: {r.json()}")
except Exception as e:
    print(f"Exception: {e}")

# Test 2: Get that successful order details
print("\n=== Test 2: Get Order Details ===")
try:
    order_id = 'BXNM4UVUQQNGR6B'
    r = requests.get(f'https://api.luno.com/api/1/orders/{order_id}', auth=(API_KEY, API_SECRET))
    print(f'HTTP {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f"Order: {data}")
    else:
        print(f"Error: {r.json()}")
except Exception as e:
    print(f"Exception: {e}")

# Test 3: List recent orders
print("\n=== Test 3: List Recent Orders ===")
try:
    r = requests.get('https://api.luno.com/api/1/listorders', auth=(API_KEY, API_SECRET), params={'state': 'COMPLETE', 'limit': 5})
    print(f'HTTP {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        orders = data.get('orders', [])
        print(f"Found {len(orders)} orders:")
        for o in orders[:3]:
            print(f"  ID: {o.get('order_id')}, Side: {o.get('side')}, Status: {o.get('state')}")
    else:
        print(f"Error: {r.json()}")
except Exception as e:
    print(f"Exception: {e}")
