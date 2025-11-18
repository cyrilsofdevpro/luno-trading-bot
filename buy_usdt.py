from luno_client import LunoClient
from dotenv import load_dotenv
import os, json, requests

load_dotenv()
API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
PAIR = 'USDTNGN'
BUDGET_NGN = float(os.getenv('BUY_BUDGET_NGN', '770'))

client = LunoClient(API_KEY, API_SECRET, dry_run=False)

# Get ticker
try:
    t = client.get_ticker(PAIR)
    ask = float(t.get('ask') or t.get('last_trade') or t.get('bid'))
    print('USDTNGN ask:', ask)
except Exception as e:
    print('Failed to fetch ticker:', e)
    raise

# Compute volume to spend approx BUDGET_NGN
# Compute volume to spend approx BUDGET_NGN
raw_volume = BUDGET_NGN / ask
# Luno requires USDT volume to be a multiple of 0.01. Floor to nearest 0.01.
volume = float(int(raw_volume / 0.01) * 0.01)
if volume <= 0:
    raise SystemExit('Computed volume is 0 after rounding. Increase budget or abort.')
print('Placing BUY for', volume, PAIR, 'roughly spending', round(volume*ask,2), 'NGN')

try:
    resp = client.place_order(PAIR, 'buy', volume, ask)
    print('Order response:', json.dumps(resp))
    # Append to trade log for dashboard visibility
    try:
        import csv, time
        log_path = os.getenv('LOG_CSV', 'trade_log.csv')
        exists = os.path.exists(log_path)
        with open(log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(['timestamp','pair','action','price','volume','details'])
            writer.writerow([time.time(), PAIR, 'buy_usdt', str(ask), str(volume), str(resp)])
        print('Logged trade to', log_path)
    except Exception as e:
        print('Failed to log trade:', e)
except Exception as e:
    resp = getattr(e, 'response', None)
    if isinstance(resp, requests.Response):
        try:
            print('ERROR JSON:', json.dumps(resp.json()))
        except Exception:
            print('ERROR TEXT:', resp.text)
    else:
        print('Exception:', str(e))
