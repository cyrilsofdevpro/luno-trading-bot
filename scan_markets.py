"""Scan candidate NGN markets and report assets affordable with a given NGN budget."""
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()
PAIR_CANDIDATES = [
    'XBTNGN',
    'ETHNGN',
    'XRPXNGN',
    'XRPNGN',
    'LTCNGN',
    'BCHNGN',
    'USDTNGN',
    'DOTNGN',
    'ADA/NGN',
]
# Some symbols may not exist on Luno; we'll try common variants.
PAIR_CANDIDATES = ['XBTNGN', 'ETHNGN', 'XRPNGN', 'LTCNGN', 'BCHNGN', 'USDTNGN']

API = 'https://api.luno.com/api/1/ticker'

budget_ngn = float(os.getenv('SCAN_BUDGET_NGN', '770'))

results = []
for pair in PAIR_CANDIDATES:
    try:
        r = requests.get(API, params={'pair': pair}, timeout=10)
        if r.status_code != 200:
            # skip unavailable pair
            continue
        t = r.json()
        # parse ask price (string)
        ask = t.get('ask') or t.get('last_trade') or t.get('bid')
        if ask is None:
            continue
        ask_f = float(ask)
        results.append({'pair': pair, 'ask': ask_f, 'raw': t})
    except Exception as e:
        # ignore errors for missing pairs
        continue

# Find which assets can be bought with budget (i.e., 1 unit cost <= budget)
affordable = [r for r in results if r['ask'] <= budget_ngn]
# Also compute minimal unit cost for fractional amount: compute max units for budget
for r in results:
    r['max_units_with_budget'] = budget_ngn / r['ask'] if r['ask']>0 else 0

print('Budget (NGN):', budget_ngn)
print('Found tickers:')
print(json.dumps(results, indent=2))
print('\nAffordable as 1 unit <= budget:')
print(json.dumps(affordable, indent=2))

# Recommend best candidate by max_units
if results:
    best = max(results, key=lambda x: x['max_units_with_budget'])
    print('\nRecommended market to consider (max units for budget):')
    print(json.dumps(best, indent=2))
else:
    print('No markets found.')
