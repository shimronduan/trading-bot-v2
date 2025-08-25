import logging
from binance.um_futures import UMFutures
from models.symbol_info import SymbolInfo
from trading_config import TRADING_CONFIG_TABLE_NAME
from utils.storage_factory import create_table_storage_client

class OrderCalculator:
    """Handles order quantity and price calculations"""
    
    def __init__(self, client: UMFutures):
        self.client = client
        self._symbol_cache = {}
    
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Get cached symbol information"""
        if symbol not in self._symbol_cache:
            exchange_info = self.client.exchange_info()
            symbol_data = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
            
            if not symbol_data:
                raise Exception(f"Could not retrieve exchange info for {symbol}")
            
            self._symbol_cache[symbol] = SymbolInfo(
                symbol=symbol,
                price_precision=int(symbol_data.get('pricePrecision', 4)),
                quantity_precision=int(symbol_data.get('quantityPrecision', 0))
            )
        
        return self._symbol_cache[symbol]
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        ticker = self.client.ticker_price(symbol)
        return float(ticker['price'])

    def calculate_trade_quantity(self, symbol: str, leverage: float, wallet_allocation: float) -> float:
        """Calculate trade quantity based on balance and leverage"""
        
        # Get USDT balance
        balances = self.client.balance()
        usdt_balance = next((float(b['balance']) for b in balances if b['asset'] == 'USDT'), 0.0)
        
        if usdt_balance == 0.0:
            raise Exception("Could not retrieve USDT balance or balance is zero.")
        
        # Get current price
        current_price = self.get_current_price(symbol)
        
        # Get symbol info
        symbol_info = self.get_symbol_info(symbol)
        
        # Calculate quantity
        trade_value_in_usdt = usdt_balance * wallet_allocation
        quantity = (trade_value_in_usdt * leverage) / current_price
        rounded_quantity = round(quantity, symbol_info.quantity_precision)
        
        logging.info(f"Available USDT: {usdt_balance:.2f}. Current Price: {current_price}. Calculated Quantity: {rounded_quantity} {symbol}.")
        
        if rounded_quantity == 0:
            raise Exception("Calculated trade quantity is zero. Insufficient balance.")
        
        # Validate minimum notional
        if rounded_quantity * current_price < symbol_info.min_notional:
            raise Exception(f"Calculated notional value ({rounded_quantity * current_price:.2f} USDT) is below the minimum required ({symbol_info.min_notional} USDT). Adjust your wallet allocation or leverage.")
        
        return rounded_quantity
