# models/trading_config_info.py

from typing import TypedDict

class TradingConfigInfo(TypedDict):
    """
    A dictionary representing the trading configuration for a symbol.
    """
    PartitionKey: str
    RowKey: str
    leverage: int
    wallet_allocation: float
    chart_time_interval: str
    atr_candles: int
