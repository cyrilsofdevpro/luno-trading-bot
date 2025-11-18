#!/usr/bin/env python3
"""Monitor the last buy and automatically sell when a profit target is reached.

Reads `trade_log.csv` to find the most recent BUY, polls the ticker for `PAIR`,
and places a SELL order via `LunoClient` when profit_before_fees >= target_pct.

Configuration (via .env):
- PAIR (e.g. USDTNGN)
- AUTO_SELL_TARGET_PCT (e.g. 2 for 2%)
- POLL_INTERVAL (seconds, default 30)
- DRY_RUN (true/false)
"""
import csv
import json
import os
import time
from dotenv import load_dotenv

from luno_client import LunoClient


def read_last_buy(csv_path="trade_log.csv"):
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    # find last row that looks like a buy
    for row in reversed(rows):
        side = (row.get('side') or row.get('action') or '').lower()
        if side in ('buy', 'b', 'bid'):
            vol = float(row.get('volume') or row.get('amount') or row.get('quantity') or 0)
            price = float(row.get('price') or row.get('execution_price') or 0)
            return {'volume': vol, 'price': price, 'order_id': row.get('order_id'), 'raw': row}
    # fallback to last row
    row = rows[-1]
    vol = float(row.get('volume') or row.get('amount') or row.get('quantity') or 0)
    price = float(row.get('price') or row.get('execution_price') or 0)
    return {'volume': vol, 'price': price, 'order_id': row.get('order_id'), 'raw': row}


def append_trade_log(row, csv_path="trade_log.csv"):
    header = ['timestamp', 'side', 'order_id', 'price', 'volume', 'note']
    exists = os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def write_state(state, state_path='bot_state.json'):
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def main():
    load_dotenv()
    PAIR = os.getenv('PAIR', 'USDTNGN')
    TARGET_PCT = float(os.getenv('AUTO_SELL_TARGET_PCT', '2.0'))
    POLL = int(os.getenv('POLL_INTERVAL', '30'))
    DRY = os.getenv('DRY_RUN', 'true').lower() == 'true'

    cli = LunoClient(os.getenv('LUNO_API_KEY'), os.getenv('LUNO_API_SECRET'), dry_run=DRY)

    last_buy = read_last_buy()
    if not last_buy or last_buy['volume'] <= 0:
        print('No previous BUY found in trade_log.csv — nothing to auto-sell.')
        return

    # If the trade log contains the pair for the buy, prefer that pair so we don't try to
    # sell the asset on a different market (this avoids huge/mismatched computations).
    csv_pair = last_buy.get('raw', {}).get('pair')
    if csv_pair:
        if csv_pair != PAIR:
            print(f"Overriding PAIR from env ({PAIR}) with pair from trade log ({csv_pair})")
        PAIR = csv_pair

    volume = last_buy['volume']
    buy_price = last_buy['price']
    spent = volume * buy_price
    print(f"Monitoring {PAIR} for auto-sell: volume={volume} bought@{buy_price} (spent {spent} NGN) target={TARGET_PCT}%")

    while True:
        ticker = cli.get_ticker(PAIR)
        bid = float(ticker.get('bid') or ticker.get('last') or ticker.get('ask'))
        current_value = bid * volume
        profit_ngn = current_value - spent
        profit_pct = (profit_ngn / spent) * 100 if spent else 0

        state = {
            'pair': PAIR,
            'bid': bid,
            'volume': volume,
            'buy_price': buy_price,
            'spent_ngn': spent,
            'current_value_ngn': current_value,
            'profit_ngn': profit_ngn,
            'profit_pct': profit_pct,
            'auto_sell_target_pct': TARGET_PCT,
        }
        write_state(state)

        print(f"bid={bid} | value={current_value:.4f} NGN | profit={profit_ngn:.4f} NGN ({profit_pct:.2f}%)")

        if profit_pct >= TARGET_PCT:
            print(f"Target reached ({profit_pct:.2f}% >= {TARGET_PCT}%), placing SELL for {volume} {PAIR}")
            # place sell at current bid as a limit order
            resp = cli.place_order(PAIR, 'sell', volume, bid, order_type='limit')
            print('Sell order response:', resp)
            # log
            append_trade_log({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                              'side': 'SELL',
                              'order_id': resp.get('order_id') or resp.get('id') or '',
                              'price': bid,
                              'volume': volume,
                              'note': f'auto_sell_target_{TARGET_PCT}pct'},)
            # update state
            state['last_sell'] = resp
            write_state(state)
            print('Auto-sell complete — exiting monitor.')
            return

        time.sleep(POLL)


if __name__ == '__main__':
    main()
