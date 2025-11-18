"""
Auto Compound Profit Mode: reinvest profits and track savings separately.
After each winning trade, split profit into reinvestment and savings.
"""
import json
import os
import logging
from typing import Dict
from datetime import datetime

LOGGER = logging.getLogger(__name__)

class CompoundManager:
    """Manage profit reinvestment and savings tracking."""
    
    STATE_FILE = 'compound_state.json'
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load compound tracking state."""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                LOGGER.warning(f"Failed to load compound state: {e}")
        
        return {
            'total_profit': 0.0,
            'total_reinvested': 0.0,
            'total_savings': 0.0,
            'transactions': [],
            'last_update': None,
        }
    
    def _save_state(self):
        """Save compound tracking state."""
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            LOGGER.info("Compound state saved")
        except Exception as e:
            LOGGER.error(f"Failed to save compound state: {e}")
    
    def record_profit_split(self, profit_ngn: float, reinvest_pct: float = 60.0, trade_id: str = None):
        """
        Record a profit and split it into reinvestment and savings.
        
        Args:
            profit_ngn: profit amount in NGN
            reinvest_pct: percentage to reinvest (0-100)
            trade_id: optional identifier for the trade
        """
        if profit_ngn <= 0:
            LOGGER.warning(f"Skipping non-positive profit: {profit_ngn}")
            return None
        
        reinvest_pct = max(0, min(100, reinvest_pct))
        reinvest_amt = profit_ngn * (reinvest_pct / 100.0)
        savings_amt = profit_ngn - reinvest_amt
        
        transaction = {
            'timestamp': datetime.now().isoformat(),
            'profit_ngn': round(profit_ngn, 2),
            'reinvest_ngn': round(reinvest_amt, 2),
            'savings_ngn': round(savings_amt, 2),
            'reinvest_pct': reinvest_pct,
            'trade_id': trade_id or '',
        }
        
        self.state['total_profit'] += profit_ngn
        self.state['total_reinvested'] += reinvest_amt
        self.state['total_savings'] += savings_amt
        self.state['last_update'] = datetime.now().isoformat()
        self.state['transactions'].append(transaction)
        
        self._save_state()
        
        LOGGER.info(f"Profit split: {profit_ngn:.2f} NGN → Reinvest: {reinvest_amt:.2f}, Savings: {savings_amt:.2f}")
        return transaction
    
    def get_total_reinvestable(self) -> float:
        """Get total amount available for reinvestment."""
        return self.state['total_reinvested']
    
    def get_total_savings(self) -> float:
        """Get total savings accumulated."""
        return self.state['total_savings']
    
    def get_stats(self) -> Dict:
        """Get compound profit statistics."""
        total_profit = self.state['total_profit']
        total_reinvested = self.state['total_reinvested']
        total_savings = self.state['total_savings']
        
        return {
            'total_profit_ngn': round(total_profit, 2),
            'total_reinvested_ngn': round(total_reinvested, 2),
            'total_savings_ngn': round(total_savings, 2),
            'reinvest_ratio_pct': round((total_reinvested / total_profit * 100) if total_profit > 0 else 0, 2),
            'transaction_count': len(self.state['transactions']),
            'last_update': self.state['last_update'],
        }
    
    def get_recent_transactions(self, limit: int = 10) -> list:
        """Get recent profit transactions."""
        return self.state['transactions'][-limit:]
    
    def reset_reinvestment_balance(self):
        """
        Reset reinvestment balance after reinvesting (call after using reinvested funds).
        Keeps savings intact.
        """
        old_reinvested = self.state['total_reinvested']
        self.state['total_reinvested'] = 0.0
        self.state['last_update'] = datetime.now().isoformat()
        self._save_state()
        LOGGER.info(f"Reinvestment balance reset (was {old_reinvested:.2f} NGN)")
