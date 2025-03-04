import pandas_ta as ta
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def calculate_indicators(data):
    required_cols = {"Close", "High", "Low"}
    
    # Ensure required columns exist
    if not required_cols.issubset(data.columns):
        missing_cols = required_cols - set(data.columns)
        logging.error(f"Missing columns: {missing_cols}. Cannot calculate indicators.")
        return data
    
    try:
        data['ema_50'] = ta.ema(data['Close'], length=50)
        data['ema_200'] = ta.ema(data['Close'], length=200)
        
        macd = ta.macd(data['Close'])
        if macd is not None:
            data['macd_line'] = macd['MACD_12_26_9']
            data['macd_signal'] = macd['MACDs_12_26_9']
        
        data['rsi'] = ta.rsi(data['Close'], length=14)
        
        stoch = ta.stoch(data['High'], data['Low'], data['Close'])
        if stoch is not None:
            data['stoch_k'] = stoch['STOCHk_14_3_3']
            data['stoch_d'] = stoch['STOCHd_14_3_3']
        
        adx = ta.adx(data['High'], data['Low'], data['Close'])
        if adx is not None:
            data['adx'] = adx['ADX_14']
            data['plus_di'] = adx['DMP_14']
            data['minus_di'] = adx['DMN_14']
        
        bollinger = ta.bbands(data['Close'], length=20, std=2)
        if bollinger is not None:
            data['upper_band'] = bollinger['BBU_20_2.0']
            data['lower_band'] = bollinger['BBL_20_2.0']

        # Fill NaN values (optional)
        data.fillna(method='bfill', inplace=True)

        logging.info("Indicators calculated successfully.")

    except Exception as e:
        logging.error(f"Error calculating indicators: {e}")

    return data
