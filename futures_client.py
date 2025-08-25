import logging
import time
from typing import Any, Dict
from binance.um_futures import UMFutures
from technical_analysis import TechnicalAnalysis
from trading_config import SYMBOL
from managers import PositionManager, OrderCalculator, TakeProfitStopLossManager
from trading_enums import TradingEnums

class FuturesClient:
    """Main futures trading client - simplified and focused"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.client = UMFutures(api_key, api_secret)
        self.position_manager = PositionManager(self.client)
        self.calculator = OrderCalculator(self.client)
        self.tp_sl_manager = TakeProfitStopLossManager(self.client, self.calculator)
    
    def manage_existing_position(self, desired_side: str) -> bool:
        """Check and manage existing positions before new trade"""
        position = self.position_manager.get_position(SYMBOL)
        
        if not position:
            logging.info("No existing position found. Proceeding with new trade.")
            return True
        
        # Check if signal matches existing position
        desired_position_side = TradingEnums.signal_to_position_side(desired_side)
        if position.side == desired_position_side:
            logging.info(f"Ignoring {desired_side} signal - {position.side} position already open")
            return False
        
        # Close opposing position
        logging.info(f"Closing opposing {position.side} position")
        return self.position_manager.close_position(position)
    
    def calculate_trade_quantity(self, config: Dict[str, Any]) -> float:
        """Calculate trade quantity - delegates to calculator"""
        leverage = config["leverage"]
        wallet_allocation = config["wallet_allocation"]
        return self.calculator.calculate_trade_quantity(SYMBOL, leverage, wallet_allocation)

    def execute_trade_with_sl_tp(self, side: str, quantity: float, tp_sl_configs: list, config: Dict[str, Any]) -> str:
        """Execute trade with stop loss and take profit orders"""
        try:
            leverage = int(config["leverage"])
            timeframe = config["chart_time_interval"]
            atr_candles = int(config["atr_candles"])
            # Get ATR for calculations
            ta_calculator = TechnicalAnalysis(client=self.client)
            atr = ta_calculator.get_atr(symbol=SYMBOL, timeframe=timeframe, length=atr_candles) or (self._get_current_price(SYMBOL) * 0.01)

            # Clean slate - cancel existing orders
            self.position_manager.cancel_all_orders(SYMBOL)
            
            # Set leverage
            self.client.change_leverage(symbol=SYMBOL, leverage=leverage)
            logging.info(f"Leverage set to {leverage}x")

            # Execute main order
            entry_price = self._execute_market_order(side, quantity)
            
            # Set TP/SL orders
            self.tp_sl_manager.create_tp_sl_orders(SYMBOL, side, entry_price, quantity, tp_sl_configs, atr)
            
            return f"Success: {side} position opened for {quantity} {SYMBOL} at ~{entry_price}"
            
        except Exception as e:
            logging.error(f"Trade execution failed: {e}")
            raise
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        ticker = self.client.ticker_price(symbol)
        return float(ticker['price'])
    
    def _execute_market_order(self, side: str, quantity: float) -> float:
        """Execute market order and return fill price"""
        main_order = self.client.new_order(symbol=SYMBOL, side=side, type='MARKET', quantity=quantity)
        order_id = main_order['orderId']
        logging.info(f"Market {side} order placed: {order_id}")
        
        # Get fill price
        for attempt in range(5):
            order_details = self.client.get_all_orders(symbol=SYMBOL, orderId=order_id)
            if order_details:
                entry_price = float(order_details[0]['avgPrice'])
                if entry_price > 0:
                    logging.info(f"Order filled at: {entry_price}")
                    return entry_price
            time.sleep(0.5)
        
        raise Exception(f"Could not verify fill price for order {order_id}")
    
    def close_all_for_symbol(self, symbol: str) -> str:
        """Close all positions and orders for symbol"""
        self.position_manager.cancel_all_orders(symbol)
        
        position = self.position_manager.get_position(symbol)
        if position:
            self.position_manager.close_position(position)
            return f"All orders cancelled and {position.side} position closed for {symbol}"
        
        return f"All orders cancelled for {symbol} (no position to close)"
    
    def cancel_orders_if_no_position(self, symbol: str) -> bool:
        """Cancel orders only if no position exists"""
        position = self.position_manager.get_position(symbol)
        if position:
            logging.info(f"Position exists for {symbol} - orders not cancelled")
            return False
        
        return self.position_manager.cancel_all_orders(symbol)
    
    def close_position_if_no_open_orders(self, symbol: str) -> bool:
        """Close position only if no open orders exist"""
        if self.position_manager.has_open_orders(symbol):
            logging.info(f"Open orders exist for {symbol} - position not closed")
            return False
        
        position = self.position_manager.get_position(symbol)
        if position:
            return self.position_manager.close_position(position)
        
        logging.info(f"No position to close for {symbol}")
        return False
