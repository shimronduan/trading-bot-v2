from dataclasses import dataclass
from trading_enums import PositionSide

@dataclass
class PositionInfo:
    """Data class for position information"""
    symbol: str
    amount: float
    side: str  # PositionSide.LONG.value or PositionSide.SHORT.value
    entry_price: float = 0.0
    
    @property
    def is_long(self) -> bool:
        return self.side == PositionSide.LONG.value
    
    @property
    def is_short(self) -> bool:
        return self.side == PositionSide.SHORT.value
