"""
Profit tracking and analytics: compute daily P/L, balances, and statistics.
"""
import csv
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

LOGGER = logging.getLogger(__name__)

class ProfitTracker:
    """Track profits, losses, and trading statistics."""
    
    def __init__(self, trade_log_path: str = 'trade_log.csv', state_file: str = 'bot_state.json'):
        self.trade_log_path = trade_log_path
        self.state_file = state_file
    
    def read_trades(self) -> List[Dict]:
        """Read all trades from trade_log.csv."""
        trades = []
        if not os.path.exists(self.trade_log_path):
            return trades
        
        try:
            with open(self.trade_log_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trades.append(row)
        except Exception as e:
            LOGGER.error(f"Failed to read trades: {e}")
        
        return trades
    
    def compute_pair_stats(self, pair: str) -> Dict:
        """Compute P/L stats for a trading pair."""
        trades = self.read_trades()
        pair_trades = [t for t in trades if t.get('pair') == pair]
        
        if not pair_trades:
            return {'pair': pair, 'trades': 0, 'total_bought': 0, 'total_sold': 0, 'pnl_ngn': 0, 'pnl_pct': 0}
        
        total_bought = 0.0
        total_sold = 0.0
        buys = []
        sells = []
        
        for t in pair_trades:
            action = t.get('action', '').lower()
            price = float(t.get('price', 0) or 0)
            volume = float(t.get('volume', 0) or 0)
            
            if 'buy' in action:
                total_bought += price * volume
                buys.append({'price': price, 'volume': volume})
            elif 'sell' in action:
                total_sold += price * volume
                sells.append({'price': price, 'volume': volume})
        
        pnl_ngn = total_sold - total_bought
        pnl_pct = (pnl_ngn / total_bought * 100) if total_bought > 0 else 0
        
        return {
            'pair': pair,
            'trades': len(pair_trades),
            'total_bought_ngn': round(total_bought, 2),
            'total_sold_ngn': round(total_sold, 2),
            'pnl_ngn': round(pnl_ngn, 2),
            'pnl_pct': round(pnl_pct, 2),
            'buy_count': len(buys),
            'sell_count': len(sells),
        }
    
    def compute_daily_pnl(self) -> Dict[str, Dict]:
        """Compute P/L grouped by day."""
        trades = self.read_trades()
        daily_stats = {}
        
        for t in trades:
            timestamp_str = t.get('timestamp', '')
            if not timestamp_str:
                continue
            
            try:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                date_key = dt.strftime('%Y-%m-%d')
            except Exception:
                continue
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {'bought': 0, 'sold': 0, 'trades': 0}
            
            action = t.get('action', '').lower()
            price = float(t.get('price', 0) or 0)
            volume = float(t.get('volume', 0) or 0)
            
            if 'buy' in action:
                daily_stats[date_key]['bought'] += price * volume
            elif 'sell' in action:
                daily_stats[date_key]['sold'] += price * volume
            
            daily_stats[date_key]['trades'] += 1
        
        # Compute P/L for each day
        for date_key in daily_stats:
            daily_stats[date_key]['pnl_ngn'] = round(daily_stats[date_key]['sold'] - daily_stats[date_key]['bought'], 2)
            daily_stats[date_key]['pnl_pct'] = (
                round(daily_stats[date_key]['pnl_ngn'] / daily_stats[date_key]['bought'] * 100, 2)
                if daily_stats[date_key]['bought'] > 0 else 0
            )
        
        return daily_stats
    
    def compute_total_stats(self) -> Dict:
        """Compute overall trading statistics."""
        trades = self.read_trades()
        
        total_bought = 0.0
        total_sold = 0.0
        pairs = set()
        
        for t in trades:
            action = t.get('action', '').lower()
            price = float(t.get('price', 0) or 0)
            volume = float(t.get('volume', 0) or 0)
            pair = t.get('pair', '')
            
            if pair:
                pairs.add(pair)
            
            if 'buy' in action:
                total_bought += price * volume
            elif 'sell' in action:
                total_sold += price * volume
        
        pnl_ngn = total_sold - total_bought
        pnl_pct = (pnl_ngn / total_bought * 100) if total_bought > 0 else 0
        
        return {
            'total_trades': len(trades),
            'unique_pairs': len(pairs),
            'total_bought_ngn': round(total_bought, 2),
            'total_sold_ngn': round(total_sold, 2),
            'pnl_ngn': round(pnl_ngn, 2),
            'pnl_pct': round(pnl_pct, 2),
            'timestamp': datetime.now().isoformat(),
        }
    
    def save_stats(self, stats_file: str = 'profit_stats.json'):
        """Compute and save all stats to a JSON file for dashboard display."""
        try:
            stats = {
                'total': self.compute_total_stats(),
                'daily': self.compute_daily_pnl(),
            }
            
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            LOGGER.info(f"Saved profit stats to {stats_file}")
            return stats
        except Exception as e:
            LOGGER.error(f"Failed to save stats: {e}")
            return {}
