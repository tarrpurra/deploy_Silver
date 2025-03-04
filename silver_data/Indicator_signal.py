import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

import logging

def generate_signals(data):
    """
    Generates Buy and Sell signals based on technical indicators with updated conditions.
    - Checks the last 48 candles for price trend (upward or downward).
    - Uses MACD, RSI, EMA, Stochastic, ADX, and DI indicators.
    - Adds additional robustness with combined conditions.
    """
    
    # Check for required columns
    required_columns = {"macd_line", "macd_signal", "rsi", "ema_50", "ema_200", "stoch_k", "stoch_d", "adx", "plus_di", "minus_di", "Close"}
    if not required_columns.issubset(data.columns):
        logging.error("Missing required columns for signal generation.")
        return data

    # Initialize signal column (0 = Hold, 1 = Buy, -1 = Sell)
    data["signal"] = 0  # Default: Hold (0)

    # Calculate trend over the last 48 candles
    data["price_trend"] = data["Close"].rolling(window=48).apply(lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1, raw=False)

    # Buy Signal Conditions
    data.loc[
        (data["price_trend"] == 1) &  # Upward trend in the last 48 candles
        (data["Close"] > data["ema_50"]) &  # Price above 50 EMA
        (data["Close"] > data["ema_200"]) &  # Price above 200 EMA
        (data["macd_line"] > data["macd_signal"]) &  # MACD line above signal line
        (data["macd_line"] > 0) &  # MACD line above zero (optional)
        (data["rsi"] > 50) &  # RSI above 50
        (data["stoch_k"] > 60) &  # Stochastic %K above 60
        (data["stoch_d"] > 50) &  # Stochastic %D above 50 (optional)
        (data["adx"] > 15) &  # ADX above 15 (trend strength)
        ((data["plus_di"] > data["minus_di"]) | (data["plus_di"].pct_change(periods=5) > 0.1)),  # +DI > -DI or recent increase
        "signal"
    ] = 1  # Buy Signal

    # Sell Signal Conditions
    data.loc[
        (data["price_trend"] == -1) &  # Downward trend in the last 48 candles
        (data["Close"] < data["ema_50"]) &  # Price below 50 EMA
        (data["Close"] < data["ema_200"]) &  # Price below 200 EMA
        (data["macd_line"] < data["macd_signal"]) &  # MACD line below signal line
        (data["macd_line"] < 0) &  # MACD line below zero (optional)
        (data["rsi"] < 55) &  # RSI below 55
        ((data["stoch_k"] < 50) | (data["stoch_d"] < 60)) &  # Stochastic %K below 50 or %D below 60
        (data["adx"] > 15) &  # ADX above 15 (trend strength)
        ((data["minus_di"] > data["plus_di"]) | (data["minus_di"].pct_change(periods=5) > 0.1)),  # -DI > +DI or recent increase
        "signal"
    ] = -1  # Sell Signal

    logging.info(f"Generated {data['signal'].value_counts().to_dict()} signals.")

    return data




