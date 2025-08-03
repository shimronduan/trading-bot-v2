# technical_analysis.py

import logging
import pandas as pd
import pandas_ta as ta
from binance.um_futures import UMFutures

class TechnicalAnalysis:
    """
    A class to handle technical analysis calculations by fetching data directly from Binance.
    """
    def __init__(self, client: UMFutures):
        """
        Initializes the TechnicalAnalysis class with a Binance Futures client.

        Args:
            client: An initialized instance of the binance.um_futures.UMFutures client.
        """
        if not client:
            raise ValueError("A valid Binance UMFutures client is required.")
        self.client = client

    def get_historical_candles(self, symbol: str, timeframe: str = '15m', limit: int = 200) -> pd.DataFrame:
        """
        Fetches historical candlestick data for a given symbol and timeframe.

        Args:
            symbol (str): The trading symbol (e.g., 'DOGEUSDT').
            timeframe (str): The candle interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d').
            limit (int): The number of candles to fetch (max 1500).

        Returns:
            A pandas DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'],
            or an empty DataFrame if an error occurs.
        """
        try:
            # Fetch raw klines data from Binance API
            # The API returns a list of lists, e.g., [timestamp, open, high, low, close, ...]
            klines = self.client.klines(symbol=symbol, interval=timeframe, limit=limit)
            
            # Define column names for clarity
            columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'quote_asset_volume', 'number_of_trades', 
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ]
            
            # Convert the raw data into a pandas DataFrame
            df = pd.DataFrame(klines, columns=columns)

            # --- Data Cleaning and Type Conversion ---
            # Select only the columns we need for TA
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Convert timestamp to a readable datetime format (optional, but good practice)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Convert price and volume columns to numeric types for calculations
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            return df

        except Exception as e:
            logging.error(f"An error occurred while fetching historical candles for {symbol}: {e}")
            # Return an empty DataFrame in case of an error
            return pd.DataFrame()

    def get_atr(self, symbol: str, timeframe: str = '15m', length: int = 14) -> float | None:
        """
        Calculates the Average True Range (ATR) for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'DOGEUSDT').
            timeframe (str): The candle interval to calculate ATR on.
            length (int): The lookback period for the ATR calculation (standard is 14).

        Returns:
            The most recent ATR value as a float, or None if the calculation fails.
        """
        logging.info(f"Calculating ATR({length}) for {symbol} on the {timeframe} timeframe.")
        
        # Fetch enough historical data for the calculation. 
        # We need at least 'length' periods, but fetching more ensures accuracy.
        df = self.get_historical_candles(symbol, timeframe, limit=length + 100)

        if df.empty or len(df) < length:
            logging.warning(f"Could not calculate ATR for {symbol}: Not enough historical data returned.")
            return None

        try:
            # Use the pandas-ta library to calculate ATR.
            # The 'append=True' argument adds the ATR column directly to our DataFrame.
            df.ta.atr(length=length, append=True)
            
            # The ATR column will be named 'ATRr_14' (for length 14).
            atr_column_name = f'ATRr_{length}'
            
            # Get the most recent ATR value (from the second to last candle, as the last one is still open)
            latest_atr = df[atr_column_name].iloc[-2]
            
            logging.info(f"Successfully calculated latest ATR for {symbol}: {latest_atr}")
            return float(latest_atr)

        except Exception as e:
            logging.error(f"An error occurred during ATR calculation for {symbol}: {e}")
            return None