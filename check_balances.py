#!/usr/bin/env python
import requests
from dotenv import dotenv_values

cfg = dotenv_values('.env')
api_key = cfg.get('LUNO_API_KEY')
api_secret = cfg.get('LUNO_API_SECRET')

# Try /accounts endpoint
try:
    resp = requests.get('https://api.luno.com/api/1/accounts', auth=(api_key, api_secret))
    resp.raise_for_status()
    accounts = resp.json()
    print('Accounts:', accounts)
except Exception as e:
    print(f'Error fetching accounts: {e}')

# Try /balance endpoint
try:
    resp = requests.get('https://api.luno.com/api/1/balance', auth=(api_key, api_secret))
    resp.raise_for_status()
    balance = resp.json()
    print('Balance response:', balance)
except Exception as e:
    print(f'Error fetching balance: {e}')
