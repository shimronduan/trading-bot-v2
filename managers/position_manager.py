import logging
from typing import Optional
from datetime import datetime, time
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
    
    def get_total_pnl(self) -> str:
        """Get total PNL for the day as a percentage of start-of-day portfolio value."""
        try:
            # Get unrealized PNL from open positions
            positions = self.client.get_position_risk()
            unrealized_pnl = sum(float(p['unRealizedProfit']) for p in positions)
            logging.info(f"Total unrealized PNL: {unrealized_pnl}")

            # Get realized PNL for the day
            today_start = datetime.combine(datetime.today(), time.min)
            start_time_ms = int(today_start.timestamp() * 1000)
            
            income_history = self.client.get_income_history(startTime=start_time_ms, incomeType='REALIZED_PNL')
            realized_pnl = sum(float(item['income']) for item in income_history)
            logging.info(f"Today's realized PNL: {realized_pnl}")

            total_pnl = unrealized_pnl + realized_pnl
            
            # Get current wallet balance to calculate start-of-day value
            account_balance = self.client.balance()
            usdt_balance = next((b for b in account_balance if b['asset'] == 'USDT'), None)
            
            if not usdt_balance:
                logging.error("Could not retrieve USDT balance.")
                return "Error"

            current_wallet_balance = float(usdt_balance['balance'])
            
            # Start of day balance = current balance - realized pnl for the day
            start_of_day_balance = current_wallet_balance - realized_pnl
            
            if start_of_day_balance == 0:
                return "0.00%"

            pnl_percentage = (total_pnl / start_of_day_balance) * 100
            
            formatted_pnl = f"{pnl_percentage:+.2f}%"
            logging.info(f"Total PNL: {total_pnl} ({formatted_pnl})")
            
            return formatted_pnl
            
        except ClientError as e:
            logging.error(f"Error fetching PNL: {e}")
            return "Error"
