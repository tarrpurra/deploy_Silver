import pandas as pd
import numpy as np

def calculate_macd(data, short_window=6, long_window=13, signal_window=5):
    """Calculate MACD with shorter window periods for faster response."""
    data['EMA_Short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_Long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD_Line'] = data['EMA_Short'] - data['EMA_Long']
    data['MACD_Signal'] = data['MACD_Line'].ewm(span=signal_window, adjust=False).mean()
    return data

def identify_trend_signals(data, trend_threshold=0.4):
    """Find buy/sell signals with increased frequency by using shorter lookbacks."""
    data = data.iloc[-48:].copy()  # Last 12-hour trading window (15m interval)
    data['5_EMA'] = data['Close'].ewm(span=3, adjust=False).mean()  # Faster EMA
    data = calculate_macd(data)

    price_change_pct = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
    nearest_support = round(min(data['Low'].iloc[-3:]), 2)  # Last 3 candles' lowest price
    nearest_resistance = round(max(data['High'].iloc[-3:]), 2)  # Last 3 candles' highest price
    last_price = data['Close'].iloc[-1]
    macd_line = data['MACD_Line'].iloc[-1]
    macd_signal = data['MACD_Signal'].iloc[-1]
    ema_5 = data['5_EMA'].iloc[-1]

    # Determine trend
    if price_change_pct > trend_threshold:
        trend = "Bullish (Uptrend)"
    elif price_change_pct < -trend_threshold:
        trend = "Bearish (Downtrend)"
    else:
        trend = "Sideways (Range-bound)"

    # ATR for volatility check
    data['TR'] = np.maximum(data['High'] - data['Low'], 
                            np.maximum(abs(data['High'] - data['Close'].shift(1)), 
                                       abs(data['Low'] - data['Close'].shift(1))))
    data['ATR'] = data['TR'].rolling(window=10).mean()
    
    volatility = data['ATR'].iloc[-1]
    price_range = nearest_resistance - nearest_support

    # More frequent buy/sell conditions
    buy_signal, sell_signal, short_signal, exit_signal = "", "", "", ""

    # Buy condition: MACD crossover and price near support
    if macd_line > macd_signal and last_price <= nearest_support * 1.03:
        buy_signal = "BUY (Fast Entry)"
    
    # Sell condition: MACD crossover down and price near resistance
    if macd_line < macd_signal and last_price >= nearest_resistance * 0.97:
        sell_signal = "SELL (Fast Exit)"
    
    # Stop Loss (Exit)
    if buy_signal and last_price < nearest_support * 0.98:
        short_signal = "SHORT (Stop Loss)"
    
    if sell_signal and last_price > nearest_resistance * 1.02:
        exit_signal = "EXIT (Stop Loss)"

    return {
        "trend": trend,
        "price_change_pct": round(price_change_pct, 2),
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "buy_signal": buy_signal or "No Buy Signal",
        "sell_signal": sell_signal or "No Sell Signal",
        "short_signal": short_signal or "No Short Signal",
        "exit_signal": exit_signal or "No Exit Signal",
        "current_price": round(last_price, 2),
        "macd_line": round(macd_line, 2),
        "macd_signal": round(macd_signal, 2),
        "5_EMA": round(ema_5, 2),
        "ATR": round(volatility, 2),
    }
