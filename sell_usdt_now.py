#!/usr/bin/env python3
"""
Sell USDT immediately at current market price.
This script will:
1. Fetch current USDT/NGN price
2. Sell all available USDT
3. Log the trade
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from luno_client import LunoClient

load_dotenv()

API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
PAIR = 'USDTNGN'
VOLUME = 0.619402  # Your current USDT balance
DRY_RUN = False  # Set to False for live trading

if not API_KEY or not API_SECRET:
    print("❌ Error: LUNO_API_KEY or LUNO_API_SECRET not set in .env")
    sys.exit(1)

print(f"🔄 Initializing Luno client (DRY_RUN={DRY_RUN})...")
client = LunoClient(API_KEY, API_SECRET, dry_run=DRY_RUN)

try:
    print(f"📊 Fetching current price for {PAIR}...")
    ticker = client.get_ticker(PAIR)
    bid = float(ticker.get('bid') or ticker.get('last') or 0)
    
    if bid <= 0:
        print(f"❌ Invalid bid price: {bid}")
        sys.exit(1)
    
    print(f"✓ Current bid: {bid} NGN per USDT")
    print(f"📈 Selling {VOLUME} USDT at {bid} = {VOLUME * bid:.2f} NGN")
    
    # Place sell order
    resp = client.place_order(
        pair=PAIR,
        side='sell',
        volume=VOLUME,
        price=bid,
        order_type='limit'
    )
    
    order_id = resp.get('order_id', 'unknown')
    print(f"\n✅ SELL ORDER PLACED!")
    print(f"   Order ID: {order_id}")
    print(f"   Pair: {PAIR}")
    print(f"   Volume: {VOLUME}")
    print(f"   Price: {bid}")
    print(f"   Expected NGN: {VOLUME * bid:.2f}")
    
    # Log the trade
    csv_path = 'trade_log.csv'
    import csv
    header = ['timestamp', 'pair', 'action', 'price', 'volume', 'details']
    exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'pair': PAIR,
            'action': 'SELL',
            'price': bid,
            'volume': VOLUME,
            'details': order_id
        })
    
    print(f"\n✅ Trade logged to {csv_path}")
    print("\n💡 Next: You can now run the auto-sell monitor to watch for price increases")
    print("   Command: python auto_sell_monitor.py")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
