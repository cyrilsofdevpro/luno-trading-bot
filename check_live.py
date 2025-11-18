from luno_client import LunoClient
from dotenv import load_dotenv
import os, json

load_dotenv()
client = LunoClient(os.getenv('LUNO_API_KEY'), os.getenv('LUNO_API_SECRET'), dry_run=True)

# Check XBTNGN ticker
try:
    t = client.get_ticker('XBTNGN')
    print('TICKER_OK:' + json.dumps(t))
except Exception as e:
    print('TICKER_ERR:' + str(e))

# Get balances
try:
    b = client.get_balances()
    print('BALANCES_OK:' + json.dumps(b))
except Exception as e:
    print('BALANCES_ERR:' + str(e))
