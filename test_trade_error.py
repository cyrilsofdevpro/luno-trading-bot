import requests
import json

# Login
session = requests.Session()
login_data = {'email': 'israelchristopher406@gmail.com', 'password': 'ISRAEL123'}
r = session.post('http://127.0.0.1:5000/login', data=login_data)
print(f"Login: {r.status_code}")

# Try to trade SOLNGN with small volume (0.001, below 0.01 minimum)
trade_data = {
    'pair': 'SOLNGN',
    'side': 'buy',
    'volume': 0.001,  # Below 0.01 minimum
    'dry_run': False
}

r = session.post('http://127.0.0.1:5000/api/trade/place', json=trade_data)
print(f"\nTrade attempt status: {r.status_code}")
print(f"Response:\n{json.dumps(r.json(), indent=2)}")
