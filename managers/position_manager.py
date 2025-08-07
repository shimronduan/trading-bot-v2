import logging
from typing import Optional
from binance.um_futures import UMFutures
from binance.error import ClientError

from models.position_info import PositionInfo
from trading_enums import PositionSide, TradingEnums

class PositionManager:
    """Handles position-related operations"""
    
    def __init__(self, client: UMFutures):
        self.client = client
    
    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """Get current position for symbol"""
        positions = self.client.get_position_risk(symbol=symbol)
        current_position = next((p for p in positions if p['symbol'] == symbol and float(p['positionAmt']) != 0), None)
        
        if not current_position:
            return None
            
        position_amt = float(current_position['positionAmt'])
        return PositionInfo(
            symbol=symbol,
            amount=abs(position_amt),
            side=PositionSide.LONG.value if position_amt > 0 else PositionSide.SHORT.value,
            entry_price=float(current_position.get('entryPrice', 0))
        )
    
    def has_open_orders(self, symbol: str) -> bool:
        """Check if symbol has any open orders"""
        try:
            open_orders = self.client.get_orders(symbol=symbol)
            return len(open_orders) > 0
        except ClientError:
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            logging.info(f"Cancelling all open orders for {symbol}")
            self.client.cancel_open_orders(symbol=symbol)
            return True
        except ClientError as e:
            logging.warning(f"Could not cancel orders for {symbol}: {e}")
            return False
    
    def close_position(self, position: PositionInfo) -> bool:
        """Close an existing position"""
        close_side = TradingEnums.position_to_close_side(position.side)
        
        try:
            self.client.new_order(
                symbol=position.symbol,
                side=close_side,
                type='MARKET',
                quantity=position.amount,
                reduceOnly=True
            )
            logging.info(f"Closed {position.side} position of {position.amount} {position.symbol}")
            return True
        except ClientError as e:
            logging.error(f"Failed to close position: {e}")
            return False
