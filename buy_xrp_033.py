#!/usr/bin/env python3
"""Buy 0.33 XRP at current ask price."""
from dotenv import load_dotenv
load_dotenv()
import os, time, csv
from luno_client import LunoClient
import requests

API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

def main():
    cli = LunoClient(API_KEY, API_SECRET, dry_run=DRY_RUN)
    pair = 'XRPNGN'
    volume = 0.33
    
    try:
        tk = cli.get_ticker(pair)
    except Exception as e:
        print('ERROR: failed to fetch ticker for', pair, e)
        return 1
    
    ask = float(tk.get('ask') or tk.get('last') or tk.get('bid'))
    estimated_ngn = volume * ask
    print(f'{pair} ask: {ask:.8f} NGN')
    print(f'Buying {volume} XRP ≈ {estimated_ngn:.2f} NGN')
    
    try:
        order_resp = cli.place_order(pair, 'buy', volume, ask, order_type='limit')
        print('Order placed:', order_resp)
    except requests.exceptions.HTTPError as he:
        try:
            print('HTTPError:', he.response.text)
        except Exception:
            print('HTTPError:', he)
        return 1
    except Exception as e:
        print('Error placing order:', e)
        return 1
    
    # Append to trade_log.csv
    row = [time.strftime('%Y-%m-%d %H:%M:%S'), pair, 'buy_xrp_033', ask, volume, str(order_resp)]
    path = 'trade_log.csv'
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['timestamp','pair','action','price','volume','details'])
        w.writerow(row)
    print('Logged trade to', path)
    print(f'Success! Bought 0.33 XRP at {ask:.2f} NGN/XRP for ≈{estimated_ngn:.2f} NGN total')
    return 0

if __name__ == '__main__':
    exit(main())
