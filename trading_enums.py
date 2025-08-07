from enum import Enum

class SignalType(Enum):
    """External signal types from webhooks/API"""
    LONG = "Long"
    SHORT = "Short"
    CLOSE = "Close"

class PositionSide(Enum):
    """Internal position side representation"""
    LONG = "LONG"
    SHORT = "SHORT"

class OrderSide(Enum):
    """Binance API order sides"""
    BUY = "BUY"
    SELL = "SELL"

class TradingEnums:
    """Utility class for trading signal and position conversions"""
    
    @staticmethod
    def signal_to_position_side(signal: str) -> str:
        """Convert external signal to internal position side"""
        if signal == SignalType.LONG.value:
            return PositionSide.LONG.value
        elif signal == SignalType.SHORT.value:
            return PositionSide.SHORT.value
        else:
            raise ValueError(f"Invalid signal type: {signal}")
    
    @staticmethod
    def signal_to_order_side(signal: str) -> str:
        """Convert external signal to Binance order side"""
        if signal == SignalType.LONG.value:
            return OrderSide.BUY.value
        elif signal == SignalType.SHORT.value:
            return OrderSide.SELL.value
        else:
            raise ValueError(f"Invalid signal type: {signal}")
    
    @staticmethod
    def position_to_close_side(position_side: str) -> str:
        """Convert position side to closing order side"""
        if position_side == PositionSide.LONG.value:
            return OrderSide.SELL.value
        elif position_side == PositionSide.SHORT.value:
            return OrderSide.BUY.value
        else:
            raise ValueError(f"Invalid position side: {position_side}")
    
    @staticmethod
    def is_valid_signal(signal: str) -> bool:
        """Check if signal is valid"""
        return signal in [SignalType.LONG.value, SignalType.SHORT.value, SignalType.CLOSE.value]
