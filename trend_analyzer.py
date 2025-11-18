"""
AI Prediction & Signal Mode: simple EMA-based trend detection and coin recommendations.
Predicts Uptrend/Downtrend/Neutral and suggests best coin to buy.
"""
import json
import os
import logging
from typing import Dict, List, Tuple, Optional
from collections import deque

LOGGER = logging.getLogger(__name__)

class TrendAnalyzer:
    """Analyze price trends using EMA and generate trading signals."""
    
    def __init__(self, short_ema_period: int = 12, long_ema_period: int = 26, signal_period: int = 9):
        """Initialize trend analyzer with EMA periods (MACD-like)."""
        self.short_period = short_ema_period
        self.long_period = long_ema_period
        self.signal_period = signal_period
        self.price_history = {}  # coin -> deque of prices
        self.max_history = 100
    
    def add_price(self, coin: str, price: float):
        """Add a price point for a coin."""
        if coin not in self.price_history:
            self.price_history[coin] = deque(maxlen=self.max_history)
        self.price_history[coin].append(price)
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None
        
        prices = list(prices)
        multiplier = 2.0 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = price * multiplier + ema * (1 - multiplier)
        
        return ema
    
    def analyze_trend(self, coin: str) -> Dict:
        """
        Analyze trend for a coin.
        Returns: {trend, ema_short, ema_long, signal_strength, momentum}
        """
        prices = list(self.price_history.get(coin, []))
        
        if len(prices) < self.long_period:
            return {
                'coin': coin,
                'trend': 'NEUTRAL',
                'signal_strength': 0,
                'momentum': 0,
                'data_points': len(prices),
                'message': f'Insufficient data ({len(prices)} prices, need {self.long_period})'
            }
        
        ema_short = self._calculate_ema(prices, self.short_period)
        ema_long = self._calculate_ema(prices, self.long_period)
        
        if ema_short is None or ema_long is None:
            return {
                'coin': coin,
                'trend': 'NEUTRAL',
                'signal_strength': 0,
                'momentum': 0,
            }
        
        # Current momentum: compare recent prices to EMAs
        current_price = prices[-1]
        momentum = ((current_price - ema_long) / ema_long) * 100
        
        # Trend determination: short EMA above/below long EMA
        if ema_short > ema_long * 1.002:  # 0.2% threshold to avoid noise
            trend = 'UPTREND'
            signal_strength = min(100, abs(momentum))
        elif ema_short < ema_long * 0.998:
            trend = 'DOWNTREND'
            signal_strength = min(100, abs(momentum))
        else:
            trend = 'NEUTRAL'
            signal_strength = 0
        
        return {
            'coin': coin,
            'trend': trend,
            'ema_short': round(ema_short, 2),
            'ema_long': round(ema_long, 2),
            'current_price': current_price,
            'momentum_pct': round(momentum, 2),
            'signal_strength': round(signal_strength, 2),
            'data_points': len(prices),
        }
    
    def get_best_buy_coin(self, coins: List[str]) -> Optional[Dict]:
        """
        Suggest best coin to buy based on strongest downtrend signal.
        Returns coin with highest buy signal strength.
        """
        if not coins:
            return None
        
        analyses = [self.analyze_trend(coin) for coin in coins]
        downtrends = [a for a in analyses if a.get('trend') == 'DOWNTREND']
        
        if not downtrends:
            # If no downtrends, suggest neutral coins with lowest prices
            return {
                'recommendation': 'HOLD',
                'message': 'No strong downtrend signals; consider waiting',
                'coins': coins,
            }
        
        # Pick downtrend with strongest signal
        best = max(downtrends, key=lambda x: x.get('signal_strength', 0))
        return {
            'recommendation': 'BUY',
            'coin': best['coin'],
            'reason': f"Strong {best['trend']} with signal strength {best['signal_strength']:.1f}%",
            'momentum': best['momentum_pct'],
            'all_signals': analyses,
        }
    
    def get_prediction_summary(self, coins: List[str]) -> Dict:
        """Get summary of all coin signals and predictions."""
        analyses = [self.analyze_trend(coin) for coin in coins]
        
        uptrends = [a for a in analyses if a.get('trend') == 'UPTREND']
        downtrends = [a for a in analyses if a.get('trend') == 'DOWNTREND']
        neutrals = [a for a in analyses if a.get('trend') == 'NEUTRAL']
        
        return {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'uptrends': uptrends,
            'downtrends': downtrends,
            'neutrals': neutrals,
            'best_buy': self.get_best_buy_coin(coins),
            'summary': {
                'total_coins': len(coins),
                'uptrending': len(uptrends),
                'downtrending': len(downtrends),
                'neutral': len(neutrals),
            }
        }
