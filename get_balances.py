from luno_client import LunoClient
from dotenv import load_dotenv
import os,json,requests

load_dotenv()
client = LunoClient(os.getenv('LUNO_API_KEY'), os.getenv('LUNO_API_SECRET'), dry_run=False)

try:
    b = client.get_balances()
    print('BALANCES_OK:' + json.dumps(b))
except Exception as e:
    resp = getattr(e, 'response', None)
    if isinstance(resp, requests.Response):
        try:
            print('BALANCES_ERR_JSON:' + json.dumps(resp.json()))
        except Exception:
            print('BALANCES_ERR_TEXT:' + resp.text)
    else:
        print('BALANCES_ERR:' + str(e))
