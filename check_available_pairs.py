#!/usr/bin/env python3
"""Check available balances on Luno account."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('LUNO_API_KEY')
api_secret = os.getenv('LUNO_API_SECRET')

if api_key and api_secret:
    # Get balance
    print("Fetching balances from Luno API...")
    resp = requests.get('https://api.luno.com/api/1/balance', auth=(api_key, api_secret), timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        balances = data.get('balance', [])
        print('\nAvailable balances:')
        print('=' * 60)
        for item in balances:
            balance = float(item.get('balance', 0))
            reserved = float(item.get('reserved', 0))
            available = balance - reserved
            if balance > 0:
                print(f"{item['asset']:10} | Balance: {balance:15.8f} | Available: {available:15.8f}")
        print('=' * 60)
        print('\nTo sell an asset, use the pair format: ASSETNGN')
        print('Example: SOLNGN (for Solana), XBTNGN (for Bitcoin)')
    else:
        print(f'Error: {resp.status_code}')
        print(resp.text)
else:
    print('API keys not found in .env')
