import logging
import time
from binance.um_futures import UMFutures
from binance.error import ClientError

from technical_analysis import TechnicalAnalysis
from trading_config import LEVERAGE, STOP_LOSS_PERCENT, SYMBOL, WALLET_ALLOCATION

class FuturesClient:
    """
    Handles interactions with Binance Futures API.
    """
    def __init__(self, api_key: str, api_secret: str):
        self.client = UMFutures(api_key, api_secret)

    def manage_existing_position(self, desired_side: str):
        """Checks for existing positions and closes them if they are opposite to the desired trade."""
        positions = self.client.get_position_risk(symbol=SYMBOL)
        current_position = next((p for p in positions if p['symbol'] == SYMBOL and float(p['positionAmt']) != 0), None)

        if not current_position:
            logging.info("No existing position found. Proceeding with new trade.")
            return True # Proceed with trade

        position_amt = float(current_position['positionAmt'])
        existing_side = 'LONG' if position_amt > 0 else 'SHORT'
        desired_action_side = 'BUY' if desired_side == 'Long' else 'SELL'
        
        # Ignore if signal is in the same direction as the open position
        if (desired_side == 'Long' and existing_side == 'LONG') or \
        (desired_side == 'Short' and existing_side == 'SHORT'):
            logging.info(f"Ignoring {desired_side} signal as a {existing_side} position is already open.")
            return False # Do not proceed

        # Close opposing position
        logging.info(f"Opposing position found. Closing existing {existing_side} position.")
        close_side = 'SELL' if existing_side == 'LONG' else 'BUY'
        self.client.new_order(symbol=SYMBOL, side=close_side, type='MARKET', quantity=abs(position_amt))
        logging.info(f"Closed {existing_side} position of {abs(position_amt)} {SYMBOL}.")
        return True # Proceed with trade

    def calculate_trade_quantity(self):
        """Calculates the trade quantity based on wallet allocation and leverage."""
        # Fetch available USDT balance
        balances = self.client.balance()
        usdt_balance = next((float(b['balance']) for b in balances if b['asset'] == 'USDT'), 0.0)
        if usdt_balance == 0.0:
            raise Exception("Could not retrieve USDT balance or balance is zero.")

        # Fetch current price
        ticker = self.client.ticker_price(SYMBOL)
        current_price = float(ticker['price'])

        # Fetch symbol precision rules
        exchange_info = self.client.exchange_info()
        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == SYMBOL), None)
        if not symbol_info:
            raise Exception(f"Could not retrieve exchange info for {SYMBOL}")
        precision = int(symbol_info['quantityPrecision'])

        # Formula: (Wallet_Balance * Allocation * Leverage) / Price
        trade_value_in_usdt = usdt_balance * WALLET_ALLOCATION
        quantity = (trade_value_in_usdt * LEVERAGE) / current_price
        
        # Round to the required precision for the symbol
        rounded_quantity = round(quantity, precision)
        logging.info(f"Available USDT: {usdt_balance:.2f}. Current Price: {current_price}. Calculated Quantity: {rounded_quantity} {SYMBOL}.")
        
        if rounded_quantity == 0:
            raise Exception("Calculated trade quantity is zero. Insufficient balance.")
            
        # Ensure the notional value meets the minimum requirement
        min_notional = 5.0  # Minimum notional value in USDT
        if rounded_quantity * current_price < min_notional:
            logging.error(f"Calculated notional value ({rounded_quantity * current_price:.2f} USDT) is below the minimum required ({min_notional} USDT). Adjust your wallet allocation or leverage.")
            raise Exception("Calculated notional value is below the minimum required. Trade cannot proceed.")
            
        return rounded_quantity

    def execute_trade_with_sl_tp(self, side: str, quantity: float, tp_sl_configs: list):
        """
        Sets leverage, places the MARKET order, confirms the fill price using the correct method,
        and then places the TAKE_PROFIT and STOP_LOSS orders.
        """
        ta_calculator = TechnicalAnalysis(client=self.client)
        atr = ta_calculator.get_atr(symbol=SYMBOL)
        
        # 1. *** NEW: Cancel all existing open orders for the symbol to prevent interference ***
        try:
            logging.info(f"Cancelling all existing open orders for {SYMBOL} to ensure a clean slate.")
            self.client.cancel_open_orders(symbol=SYMBOL)
        except ClientError as e:
            # Don't stop the whole trade if cancellation fails, but log it as a warning.
            # This might happen if there are no open orders, which is fine.
            logging.warning(f"Could not cancel all open orders (this is often okay): {e}")

        # 2. Set Leverage
        self.client.change_leverage(symbol=SYMBOL, leverage=LEVERAGE)
        logging.info(f"Leverage set to {LEVERAGE}x for {SYMBOL}.")

        # 3. Place Main MARKET Order
        main_order = self.client.new_order(symbol=SYMBOL, side=side, type='MARKET', quantity=quantity)
        order_id = main_order['orderId']
        logging.info(f"Main {side} order sent: orderId={order_id}")

        # 4. *** CORRECTED: Get the actual fill price using get_all_orders ***
        try:
            max_retries = 5
            order_details_list = []
            for attempt in range(max_retries):
                order_details_list = self.client.get_all_orders(symbol=SYMBOL, orderId=order_id)
                if order_details_list:
                    break
                time.sleep(0.5)  # Wait half a second before retrying

            # The API returns a list, even for a single orderId.
            if not order_details_list:
                raise Exception(f"Could not retrieve details for order {order_id}. The returned list was empty.")
            
            filled_order = order_details_list[0]
            entry_price = float(filled_order['avgPrice'])

            # Sanity check to ensure we have a valid price
            if entry_price <= 0:
                raise Exception(f"Failed to get a valid average price for order {order_id}. avgPrice reported as {entry_price}.")
            
            logging.info(f"Order {order_id} confirmed filled at average price: {entry_price}")

        except Exception as e:
            logging.error(f"Could not verify fill price for order {order_id}. Error: {e}")
            # If we can't verify the price, we cannot safely set SL/TP.
            raise  # Re-raise the exception to be caught by the main handler

        # 5. *** NEW: Calculate and place multiple Take Profit orders and one Stop Loss ***
        close_side = 'SELL' if side == 'BUY' else 'BUY'
        
        # Get symbol precision rules for quantity and price
        exchange_info = self.client.exchange_info()
        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == SYMBOL), None)
        
        if not symbol_info:
            raise Exception(f"Could not retrieve exchange info for {SYMBOL}")
        
        price_decimals = int(symbol_info.get('pricePrecision', 4))
        quantity_decimals = int(symbol_info.get('quantityPrecision', 0))

        # --- Define Take Profit levels ---
        tp_list = [record for record in tp_sl_configs if str(record.get('PartitionKey', '')).lower() == 'tp'  and str(record.get('close_fraction', '')).lower() != '']
        sl_list = [record for record in tp_sl_configs if str(record.get('PartitionKey', '')).lower() == 'sl'  and str(record.get('close_fraction', '')).lower() != '']
        last_tp_atr = [float(record.get('atr_multiple', 0)) for record in tp_sl_configs if str(record.get('PartitionKey', '')).lower() == 'tp' and str(record.get('close_fraction', '')).lower() == '']
        last_sl = [float(record.get('atr_multiple', 0)) for record in tp_sl_configs if str(record.get('PartitionKey', '')).lower() == 'sl' and str(record.get('close_fraction', '')).lower() == '']

        tp_levels = []
        for record in tp_list:
            try:
                atr_multiple = float(record.get('atr_multiple', 0))
                close_fraction = float(record.get('close_fraction', 0))/100  # Convert percentage to decimal
                tp_levels.append({"atr_multiple": atr_multiple, "close_fraction": close_fraction})
            except ValueError as e:
                logging.error(f"Invalid TP record: {record}. Error: {e}")

        sl_levels = []
        for record in sl_list:
            try:
                atr_multiple = float(record.get('atr_multiple', 0))
                close_fraction = float(record.get('close_fraction', 0))/100  # Convert percentage to decimal
                sl_levels.append({"atr_multiple": atr_multiple, "close_fraction": close_fraction})
            except ValueError as e:
                logging.error(f"Invalid SL record: {record}. Error: {e}")

        remaining_quantity = quantity
        
        # --- Place multiple Take Profit orders ---
        # Ensure each take profit order meets the minimum notional value
        min_notional = 5.0  # Minimum notional value in USDT
        
        # Safety check for ATR value
        if atr is None or atr <= 0:
            logging.warning("ATR value is None or invalid. Using fallback ATR calculation.")
            # Fallback: use 1% of entry price as ATR estimate
            atr = entry_price * 0.01
            
        for i, level in enumerate(tp_levels):
            tp_quantity = round(quantity * level['close_fraction'], quantity_decimals)
            # Calculate TP price using ATR: entry_price +/- (atr * atr_multiple)
            tp_price = f"{entry_price + (atr * level['atr_multiple']) if side == 'BUY' else entry_price - (atr * level['atr_multiple']):.{price_decimals}f}"

            # Skip orders that do not meet the minimum notional value
            if tp_quantity * float(tp_price) < min_notional:
                logging.warning(f"Skipping Take Profit order #{i+1} as its notional value is below the minimum required ({min_notional} USDT).")
                continue

            self.client.new_order(
                symbol=SYMBOL,
                side=close_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp_price,
                quantity=tp_quantity  # Specify quantity for partial close
            )
            logging.info(f"Take Profit order #{i+1} placed: close {tp_quantity} at {tp_price}.")
            remaining_quantity -= tp_quantity

        # --- Place final Take Profit for the remaining amount ---
        # This ensures any rounding differences are handled in the last TP
        if len(last_tp_atr) > 0 and remaining_quantity > 0:
            # Calculate final TP price using ATR: entry_price +/- (atr * atr_multiple)
            last_tp_price = f"{entry_price + (atr * last_tp_atr[0]) if side == 'BUY' else entry_price - (atr * last_tp_atr[0]):.{price_decimals}f}"

            if remaining_quantity * float(last_tp_price) >= min_notional:
                self.client.new_order(
                    symbol=SYMBOL,
                    side=close_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=last_tp_price,
                    quantity=round(remaining_quantity, quantity_decimals)
                )
                logging.info(f"Take Profit order #3 (remaining) placed: close {round(remaining_quantity, quantity_decimals)} at {last_tp_price}.")
            else:
                logging.warning(f"Skipping final Take Profit order as its notional value is below the minimum required ({min_notional} USDT).")
        
        # --- Place a single Stop Loss for the entire position ---
        if side == 'BUY':
            sl_price = f"{entry_price * (1 - STOP_LOSS_PERCENT):.{price_decimals}f}"
        else: # SELL
            sl_price = f"{entry_price * (1 + STOP_LOSS_PERCENT):.{price_decimals}f}"

        # --- Place a single Trailing Stop Loss for the entire position ---
        if atr is not None and entry_price > 0:
            # Calculate callbackRate as a percentage of entry price
            callback_rate = round((atr*1.5 / entry_price) * 100, 2)
            # Binance minimum callbackRate is usually 0.1, so ensure it's not below that
            callback_rate = max(callback_rate, 0.1)
        else:
            callback_rate = 0.5  # fallback to default

        self.client.new_order(
            symbol=SYMBOL,
            side=close_side,
            type='TRAILING_STOP_MARKET',
            quantity=quantity,
            callbackRate=callback_rate,
            reduceOnly=True
        )

        return f"Success: {side} position opened for {quantity} {SYMBOL} at ~{entry_price}. Multiple TPs and one SL have been set."
    
    def close_all_for_symbol(self, symbol: str):
        """
        Closes any open position and cancels all open orders for a given symbol.
        """
        # First, cancel all open orders to prevent any unwanted fills
        try:
            logging.info(f"Cancelling all open orders for {symbol}...")
            self.client.cancel_open_orders(symbol=symbol)
            logging.info("All open orders cancelled.")
        except ClientError as e:
            logging.warning(f"Could not cancel all open orders (this is often okay if none exist): {e}")

        # Second, check for an open position
        positions = self.client.get_position_risk(symbol=symbol)
        current_position = next((p for p in positions if p['symbol'] == symbol and float(p['positionAmt']) != 0), None)

        if not current_position:
            logging.info(f"No open position found for {symbol}.")
            return "No open position to close."

        # If a position exists, close it with a market order
        position_amt = float(current_position['positionAmt'])
        existing_side = 'LONG' if position_amt > 0 else 'SHORT'
        close_side = 'SELL' if existing_side == 'LONG' else 'BUY'
        
        logging.info(f"Closing {existing_side} position of {abs(position_amt)} {symbol}...")
        self.client.new_order(
            symbol=symbol,
            side=close_side,
            type='MARKET',
            quantity=abs(position_amt),
            reduceOnly=True # Ensures this order only reduces a position
        )
        
        message = f"Close signal received. All orders for {symbol} cancelled and position closed."
        logging.info(message)
        return message
    
    def cancel_orders_if_no_position(self, symbol: str):
        """
        Cancels all open orders for a given symbol, but only if there is no open position.
        """
        # Check for an open position first
        try:
            positions = self.client.get_position_risk(symbol=symbol)
            position_exists = any(p['symbol'] == symbol and float(p['positionAmt']) != 0 for p in positions)

            if position_exists:
                message = f"An open position exists for {symbol}. Orders will not be cancelled."
                logging.info(message)
                return False
            
            # If no position exists, proceed to cancel orders
            logging.info(f"No open position for {symbol}. Proceeding to cancel all open orders.")
            self.client.cancel_open_orders(symbol=symbol)
            message = f"Successfully cancelled all open orders for {symbol} as no position was found."
            logging.info(message)
            return True

        except ClientError as e:
            # This might happen if there are no open orders, which is not a critical failure.
            if e.error_code == -2011: # "Unknown order sent." can indicate no orders to cancel
                    message = f"No open orders found for {symbol} to cancel."
                    logging.info(message)
                    return message
            logging.error(f"An error occurred while trying to cancel orders for {symbol}: {e}")
            raise  # Re-raise other client errors
        except Exception as e:
            logging.error(f"An unexpected error occurred in cancel_orders_if_no_position for {symbol}: {e}")

    def close_position_if_no_open_orders(self, symbol: str):
        """
        Closes an open position for a symbol if and only if there are no open orders for it.
        """
        try:
            # 1. Check for any open orders for the symbol
            open_orders = self.client.get_orders(symbol=symbol)
            if open_orders:
                message = f"Found {len(open_orders)} open order(s) for {symbol}. Position will not be closed."
                logging.info(message)
                return False

            logging.info(f"No open orders found for {symbol}. Checking for an open position.")

            # 2. If no open orders, check for an open position
            positions = self.client.get_position_risk(symbol=symbol)
            current_position = next((p for p in positions if p['symbol'] == symbol and float(p['positionAmt']) != 0), None)

            if not current_position:
                message = f"No open position found for {symbol} to close."
                logging.info(message)
                return False

            # 3. If a position exists and there are no orders, close it
            position_amt = float(current_position['positionAmt'])
            existing_side = 'LONG' if position_amt > 0 else 'SHORT'
            close_side = 'SELL' if existing_side == 'LONG' else 'BUY'
            
            logging.info(f"Closing {existing_side} position of {abs(position_amt)} {symbol} as no open orders were found...")
            self.client.new_order(
                symbol=symbol,
                side=close_side,
                type='MARKET',
                quantity=abs(position_amt),
                reduceOnly=True # Ensures this order only reduces a position
            )
            
            message = f"Successfully closed position for {symbol}."
            logging.info(message)
            return True

        except ClientError as e:
            logging.error(f"A client error occurred while trying to close position for {symbol}: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred in close_position_if_no_open_orders for {symbol}: {e}")
            raise
