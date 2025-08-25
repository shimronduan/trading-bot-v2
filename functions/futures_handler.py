from trading_config import SYMBOL, TP_SL_TABLE_NAME, TRADING_CONFIG_TABLE_NAME
from utils.client_factory import create_futures_client
from utils.storage_factory import create_table_storage_client, create_queue_client
from trading_enums import TradingEnums, SignalType
import base64
import logging

def handle_futures(signal_type):
    client = create_futures_client()
    ats_client = create_table_storage_client(TP_SL_TABLE_NAME)
    response_message = ""
    if signal_type == SignalType.CLOSE.value:
        response_message = client.close_all_for_symbol(symbol=SYMBOL)
    else:
        desired_side = TradingEnums.signal_to_order_side(signal_type)
        should_proceed = client.manage_existing_position(signal_type)

        if not should_proceed:
            logging.warning(f"Signal {signal_type} ignored due to existing position.")
            return f"Signal {signal_type} ignored due to existing position."
        trading_config_client = create_table_storage_client(TRADING_CONFIG_TABLE_NAME)
        trading_config = trading_config_client.read_record(SYMBOL, SYMBOL)
        
        if trading_config is None:
            raise Exception(f"Trading config for symbol '{SYMBOL}' not found.")
        
        quantity = client.calculate_trade_quantity(trading_config)
        records = ats_client.list_records()
        response_message = client.execute_trade_with_sl_tp(desired_side, quantity, records, trading_config)

        try:
            queue_client = create_queue_client(queue_name="orders")
            encoded_message = base64.b64encode("DOGEUSDT".encode("utf-8")).decode("utf-8")
            queue_client.send_message(encoded_message, visibility_timeout=60)
            logging.info("Successfully enqueued message: DOGEUSDT")
        except Exception as e:
            logging.error(f"Failed to enqueue message. Error: {e}", exc_info=True)
    return response_message
    