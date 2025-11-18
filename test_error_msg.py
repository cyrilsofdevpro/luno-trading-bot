from luno_client import LunoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = LunoClient(os.getenv('LUNO_API_KEY'), os.getenv('LUNO_API_SECRET'), dry_run=False)

try:
    resp = client.place_order('XBTNGN', 'buy', 0.001, 70000000)
    print('Success:', resp)
except Exception as e:
    print('Error message:', str(e))
