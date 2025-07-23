import os

def get_env_variables():
    """
    Returns a dictionary of environment variables for the given names.
    If a variable is not set, its value will be None.
    """
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    TRADING_STATE_TABLE_NAME = "TradingBotState"
    TP_SL_TABLE_NAME = "TakeProfitAndStopLoss"
    if not API_KEY or not API_SECRET or not AZURE_STORAGE_CONNECTION_STRING:
        raise ValueError("One or more required environment variables are not set.")
    return {
        "API_KEY": API_KEY,
        "API_SECRET": API_SECRET,
        "AZURE_STORAGE_CONNECTION_STRING": AZURE_STORAGE_CONNECTION_STRING,
        "TRADING_STATE_TABLE_NAME": TRADING_STATE_TABLE_NAME,
        "TP_SL_TABLE_NAME": TP_SL_TABLE_NAME
    }