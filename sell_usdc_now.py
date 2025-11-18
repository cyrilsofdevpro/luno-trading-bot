#!/usr/bin/env python3
"""
Sell USDC immediately at current market price and monitor it.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from luno_client import LunoClient
import csv

load_dotenv()

API_KEY = os.getenv('LUNO_API_KEY')
API_SECRET = os.getenv('LUNO_API_SECRET')
PAIR = 'USDCNGN'
VOLUME = 0.034084  # Your current USDC balance
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
    
    print(f"✓ Current bid: {bid} NGN per USDC")
    print(f"📈 Selling {VOLUME} USDC at {bid} = {VOLUME * bid:.2f} NGN")
    
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
    print("\n💡 Next: The auto-sell monitor will watch this USDC and track price changes")
    print("   Command: python auto_sell_monitor.py")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
