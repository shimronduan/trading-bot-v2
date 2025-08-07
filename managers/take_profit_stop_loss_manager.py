import logging
from typing import List, Dict, Optional
from binance.um_futures import UMFutures
from binance.error import ClientError

from models.symbol_info import SymbolInfo
from managers.order_calculator import OrderCalculator
from trading_enums import OrderSide

class TakeProfitStopLossManager:
    """Handles TP/SL order creation"""
    
    def __init__(self, client: UMFutures, calculator: OrderCalculator):
        self.client = client
        self.calculator = calculator
    
    def create_tp_sl_orders(self, symbol: str, side: str, entry_price: float, 
                          quantity: float, tp_sl_configs: List[Dict], atr: float):
        """Create take profit and stop loss orders"""
        symbol_info = self.calculator.get_symbol_info(symbol)
        close_side = OrderSide.SELL.value if side == OrderSide.BUY.value else OrderSide.BUY.value
        
        # Parse configurations
        tp_levels = self._parse_tp_levels(tp_sl_configs)
        last_tp_atr = self._get_last_tp_atr(tp_sl_configs)
        trailing_sl_atr = self._get_trailing_sl_atr(tp_sl_configs)
        
        # Create TP orders
        remaining_quantity = self._create_tp_orders(symbol, close_side, entry_price, quantity, tp_levels, atr, symbol_info)
        
        # Create final TP for remaining quantity
        if last_tp_atr and remaining_quantity > 0:
            self._create_final_tp(symbol, close_side, entry_price, remaining_quantity, last_tp_atr, atr, symbol_info)
        
        # Create trailing SL if configured
        if trailing_sl_atr:
            self._create_trailing_sl(symbol, close_side, entry_price, quantity, trailing_sl_atr, atr)
    
    def _parse_tp_levels(self, configs: List[Dict]) -> List[Dict]:
        """Parse TP levels from configuration"""
        tp_levels = []
        tp_list = [record for record in configs 
                  if str(record.get('PartitionKey', '')).lower() == 'tp' 
                  and str(record.get('close_fraction', '')).lower() != '']
        
        for record in tp_list:
            try:
                atr_multiple = float(record.get('atr_multiple', 0))
                close_fraction = float(record.get('close_fraction', 0)) / 100
                tp_levels.append({"atr_multiple": atr_multiple, "close_fraction": close_fraction})
            except ValueError as e:
                logging.error(f"Invalid TP record: {record}. Error: {e}")
        return tp_levels
    
    def _get_last_tp_atr(self, configs: List[Dict]) -> Optional[float]:
        """Get last TP ATR multiplier"""
        last_tp_atr = [float(record.get('atr_multiple', 0)) for record in configs 
                      if str(record.get('PartitionKey', '')).lower() == 'tp' 
                      and str(record.get('close_fraction', '')).lower() == '']
        return last_tp_atr[0] if last_tp_atr else None
    
    def _get_trailing_sl_atr(self, configs: List[Dict]) -> Optional[float]:
        """Get trailing stop loss ATR multiplier"""
        trailing_sl_atr = [float(record.get('atr_multiple', 0)) for record in configs 
                          if str(record.get('PartitionKey', '')).lower() == 'tsl' 
                          and str(record.get('close_fraction', '')).lower() == '']
        return trailing_sl_atr[0] if trailing_sl_atr else None
    
    def _create_tp_orders(self, symbol: str, close_side: str, entry_price: float, 
                         quantity: float, tp_levels: List[Dict], atr: float, symbol_info: SymbolInfo) -> float:
        """Create multiple take profit orders and return remaining quantity"""
        remaining_quantity = quantity
        
        for i, level in enumerate(tp_levels):
            tp_quantity = round(quantity * level['close_fraction'], symbol_info.quantity_precision)
            
            # Calculate TP price
            if close_side == OrderSide.SELL.value:  # Long position
                tp_price = entry_price + (atr * level['atr_multiple'])
            else:  # Short position
                tp_price = entry_price - (atr * level['atr_multiple'])
            
            tp_price_str = f"{tp_price:.{symbol_info.price_precision}f}"
            
            # Check minimum notional
            if tp_quantity * tp_price < symbol_info.min_notional:
                logging.warning(f"Skipping Take Profit order #{i+1} as its notional value is below the minimum required ({symbol_info.min_notional} USDT).")
                continue
            
            try:
                self.client.new_order(
                    symbol=symbol,
                    side=close_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=tp_price_str,
                    quantity=tp_quantity
                )
                logging.info(f"Take Profit order #{i+1} placed: close {tp_quantity} at {tp_price_str}")
                remaining_quantity -= tp_quantity
            except ClientError as e:
                logging.error(f"Failed to place TP order #{i+1}: {e}")
        
        return remaining_quantity
    
    def _create_final_tp(self, symbol: str, close_side: str, entry_price: float, 
                        remaining_quantity: float, last_tp_atr: float, atr: float, symbol_info: SymbolInfo):
        """Create final TP order for remaining quantity"""
        if close_side == OrderSide.SELL.value:  # Long position
            last_tp_price = entry_price + (atr * last_tp_atr)
        else:  # Short position
            last_tp_price = entry_price - (atr * last_tp_atr)
        
        last_tp_price_str = f"{last_tp_price:.{symbol_info.price_precision}f}"
        
        if remaining_quantity * last_tp_price >= symbol_info.min_notional:
            try:
                self.client.new_order(
                    symbol=symbol,
                    side=close_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=last_tp_price_str,
                    quantity=round(remaining_quantity, symbol_info.quantity_precision)
                )
                logging.info(f"Take Profit order #final (remaining) placed: close {round(remaining_quantity, symbol_info.quantity_precision)} at {last_tp_price_str}")
            except ClientError as e:
                logging.error(f"Failed to place final TP order: {e}")
        else:
            logging.warning(f"Skipping final Take Profit order as its notional value is below the minimum required ({symbol_info.min_notional} USDT).")
    
    def _create_trailing_sl(self, symbol: str, close_side: str, entry_price: float, 
                           quantity: float, trailing_sl_atr: float, atr: float):
        """Create trailing stop loss order"""
        callback_rate = max(round((atr * trailing_sl_atr / entry_price) * 100, 2), 0.1)
        
        try:
            self.client.new_order(
                symbol=symbol,
                side=close_side,
                type='TRAILING_STOP_MARKET',
                quantity=quantity,
                callbackRate=callback_rate,
                reduceOnly=True
            )
            logging.info(f"Trailing SL placed with callback rate: {callback_rate}%")
        except ClientError as e:
            logging.error(f"Failed to place trailing SL: {e}")
