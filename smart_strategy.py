"""
Smart trading strategy: auto buy/sell with price triggers, profit targets, and stop-loss.
Supports multiple coins with configurable thresholds.
"""
import json
import os
import logging
from typing import Dict, Optional, List

LOGGER = logging.getLogger(__name__)

class SmartStrategy:
    """Configurable smart trading strategy with multiple coin support."""
    
    CONFIG_FILE = 'strategy_config.json'
    
    # Default thresholds (can be overridden per coin)
    DEFAULTS = {
        'buy_drop_pct': 3.0,        # Buy when price drops X%
        'sell_profit_pct': 10.0,    # Sell at X% profit
        'stop_loss_pct': 5.0,       # Cut losses at X% loss
        'compound_reinvest_pct': 60.0,  # Reinvest X% of profits
        'enabled': True,
    }
    
    # Supported coins on Luno
    SUPPORTED_COINS = ['BTCNGN', 'XRPNGN', 'SOLNGN', 'ETHNGN', 'USDCNGN', 'USDTNGN']
    
    def __init__(self, config_file: str = None):
        """Initialize strategy with config file."""
        self.config_file = config_file or self.CONFIG_FILE
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load strategy config from JSON file or create defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    cfg = json.load(f)
                    LOGGER.info(f"Loaded strategy config from {self.config_file}")
                    return cfg
            except Exception as e:
                LOGGER.warning(f"Failed to load config: {e}. Using defaults.")
        
        # Create default config for all supported coins
        default_config = {
            'active_coin': 'USDTNGN',
            'coins': {}
        }
        for coin in self.SUPPORTED_COINS:
            default_config['coins'][coin] = self.DEFAULTS.copy()
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, cfg: Dict):
        """Save config to JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(cfg, f, indent=2)
            LOGGER.info(f"Saved strategy config to {self.config_file}")
        except Exception as e:
            LOGGER.error(f"Failed to save config: {e}")
    
    def get_active_coin(self) -> str:
        """Get currently active trading coin."""
        return self.config.get('active_coin', 'USDTNGN')
    
    def set_active_coin(self, coin: str):
        """Set the active trading coin."""
        if coin not in self.SUPPORTED_COINS:
            raise ValueError(f"Unsupported coin: {coin}. Supported: {self.SUPPORTED_COINS}")
        self.config['active_coin'] = coin
        self._save_config(self.config)
        LOGGER.info(f"Active coin set to {coin}")
    
    def get_coin_config(self, coin: str = None) -> Dict:
        """Get strategy config for a coin."""
        if coin is None:
            coin = self.get_active_coin()
        
        if coin not in self.config.get('coins', {}):
            # Lazy-init if missing
            if 'coins' not in self.config:
                self.config['coins'] = {}
            self.config['coins'][coin] = self.DEFAULTS.copy()
            self._save_config(self.config)
        
        return self.config['coins'][coin]
    
    def update_coin_config(self, coin: str, **kwargs):
        """Update strategy config for a coin."""
        if coin not in self.SUPPORTED_COINS:
            raise ValueError(f"Unsupported coin: {coin}")
        
        cfg = self.get_coin_config(coin)
        cfg.update(kwargs)
        self.config['coins'][coin] = cfg
        self._save_config(self.config)
        LOGGER.info(f"Updated config for {coin}: {kwargs}")
    
    def should_buy(self, current_price: float, baseline_price: float, coin: str = None) -> bool:
        """Check if price has dropped enough to trigger a buy."""
        cfg = self.get_coin_config(coin)
        if not cfg.get('enabled', True):
            return False
        
        drop_pct = cfg.get('buy_drop_pct', self.DEFAULTS['buy_drop_pct'])
        price_drop_pct = ((baseline_price - current_price) / baseline_price) * 100
        
        result = price_drop_pct >= drop_pct
        if result:
            LOGGER.info(f"{coin or 'active'}: price dropped {price_drop_pct:.2f}% (threshold: {drop_pct}%) → BUY signal")
        return result
    
    def should_sell(self, current_price: float, buy_price: float, coin: str = None) -> tuple:
        """
        Check if price has risen enough to trigger a sell or hit stop-loss.
        Returns: (should_sell, reason)
        """
        cfg = self.get_coin_config(coin)
        if not cfg.get('enabled', True):
            return False, None
        
        profit_pct = ((current_price - buy_price) / buy_price) * 100
        target_profit = cfg.get('sell_profit_pct', self.DEFAULTS['sell_profit_pct'])
        stop_loss = cfg.get('stop_loss_pct', self.DEFAULTS['stop_loss_pct'])
        
        if profit_pct >= target_profit:
            LOGGER.info(f"{coin or 'active'}: profit {profit_pct:.2f}% (target: {target_profit}%) → SELL signal (profit target)")
            return True, f"profit_target ({profit_pct:.2f}%)"
        
        if profit_pct <= -stop_loss:
            LOGGER.warning(f"{coin or 'active'}: loss {profit_pct:.2f}% (max loss: {stop_loss}%) → SELL signal (stop-loss)")
            return True, f"stop_loss ({profit_pct:.2f}%)"
        
        return False, None
    
    def get_reinvest_amounts(self, profit_ngn: float, coin: str = None) -> tuple:
        """
        Calculate reinvest and savings amounts from profit.
        Returns: (reinvest_ngn, savings_ngn)
        """
        cfg = self.get_coin_config(coin)
        reinvest_pct = cfg.get('compound_reinvest_pct', self.DEFAULTS['compound_reinvest_pct']) / 100.0
        reinvest = profit_ngn * reinvest_pct
        savings = profit_ngn - reinvest
        return reinvest, savings
    
    def list_coins(self) -> List[str]:
        """Return list of supported coins."""
        return self.SUPPORTED_COINS
