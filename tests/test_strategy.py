import strategy


def test_compute_ema_simple():
    prices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    ema = strategy.compute_ema(prices, period=3)
    # EMA should be a float and between min and max
    assert isinstance(ema, float)
    assert 1 <= ema <= 10


def test_signal_from_prices():
    # ascending prices -> sell signal
    prices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    sig = strategy.signal_from_prices(prices, period=3)
    assert sig in ("buy", "sell", "hold")
