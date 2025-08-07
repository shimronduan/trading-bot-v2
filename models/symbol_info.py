from dataclasses import dataclass

@dataclass
class SymbolInfo:
    """Data class for symbol trading information"""
    symbol: str
    price_precision: int
    quantity_precision: int
    min_notional: float = 5.0
