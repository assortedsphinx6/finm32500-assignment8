# tests/test_strategy_logic.py
import statistics

SHORT_WIN = 5
LONG_WIN = 15
BULLISH_THRESHOLD = 60
BEARISH_THRESHOLD = 40

def ma(values, n):
    if len(values) == 0:
        return 0.0
    return sum(values[-n:]) / min(len(values), n)

def price_signal(prices):
    s_ma = ma(prices, SHORT_WIN)
    l_ma = ma(prices, LONG_WIN)
    return "BUY" if s_ma > l_ma else "SELL"

def news_signal(sentiment):
    if sentiment > BULLISH_THRESHOLD:
        return "BUY"
    if sentiment < BEARISH_THRESHOLD:
        return "SELL"
    return "HOLD"

def test_price_and_news_signals_buy_sell_neutral():
    # rising prices -> price BUY
    prices_rise = [100 + i for i in range(20)]
    assert price_signal(prices_rise) == "BUY"

    # falling prices -> price SELL
    prices_fall = [200 - i for i in range(20)]
    assert price_signal(prices_fall) == "SELL"

    # news signals
    assert news_signal(80) == "BUY"
    assert news_signal(20) == "SELL"
    assert news_signal(50) == "HOLD"
