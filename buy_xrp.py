from dotenv import load_dotenv
load_dotenv()
import os, math, time, csv
from luno_client import LunoClient
import requests

API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

def main():
    cli = LunoClient(API_KEY, API_SECRET, dry_run=DRY_RUN)
    pair = 'XRPNGN'
    try:
        tk = cli.get_ticker(pair)
    except Exception as e:
        print('ERROR: failed to fetch ticker for', pair, e)
        return 2

    ask = float(tk.get('ask') or tk.get('last') or tk.get('bid'))
    budget = 400.0
    raw_vol = budget / ask
    print(f'{pair} ask: {ask:.8f} NGN — raw volume for {budget} NGN = {raw_vol:.8f}')

    # Try sensible step sizes from fine to coarse until an order succeeds
    steps = [0.0001, 0.001, 0.01, 0.1, 1]
    order_resp = None
    for step in steps:
        vol = math.floor(raw_vol / step) * step
        vol = round(vol, 8)
        if vol <= 0:
            continue
        print(f'Trying volume {vol} (step {step})')
        try:
            order_resp = cli.place_order(pair, 'buy', vol, ask, order_type='limit')
            print('Order placed:', order_resp)
            break
        except requests.exceptions.HTTPError as he:
            try:
                print('HTTPError:', he.response.text)
            except Exception:
                print('HTTPError:', he)
        except Exception as e:
            print('Error placing order:', e)

    if not order_resp:
        print('No order placed. Try increasing budget or check pair availability.')
        return 1

    # Append to trade_log.csv
    row = [time.strftime('%Y-%m-%d %H:%M:%S'), pair, 'buy_xrp', ask, order_resp.get('volume') if isinstance(order_resp, dict) else vol, str(order_resp)]
    path = 'trade_log.csv'
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['timestamp','pair','action','price','volume','details'])
        w.writerow(row)
    print('Logged trade to', path)
    return 0

if __name__ == '__main__':
    exit(main())
