"""Strategy helpers: EMA calculation and simple signal generation."""
from typing import List, Optional
import pandas as pd


def compute_ema(prices: List[float], period: int = 10) -> Optional[float]:
    """Compute EMA over a list of prices using pandas. Returns last EMA value or None if insufficient data."""
    if not prices or len(prices) < 2:
        return None
    s = pd.Series(prices)
    ema = s.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])


def signal_from_prices(prices: List[float], period: int = 10) -> str:
    """Return a simple signal: 'buy', 'sell' or 'hold'.

    - buy: last price is below EMA
    - sell: last price is above EMA
    - hold: insufficient data or price == ema
    """
    if len(prices) < 2:
        return "hold"

    ema = compute_ema(prices, period)
    if ema is None:
        return "hold"

    last_price = prices[-1]
    if last_price < ema:
        return "buy"
    if last_price > ema:
        return "sell"
    return "hold"
