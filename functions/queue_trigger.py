import azure.functions as func
import logging
import base64
from utils.client_factory import create_futures_client
from azure.storage.queue import QueueClient

from utils.storage_factory import create_queue_client

def main(msg: func.QueueMessage):
    try:
        ticker_symbol_bytes = msg.get_body()
        ticker_symbol = ticker_symbol_bytes.decode('utf-8', errors='replace').strip()
        client = create_futures_client() 
        closedPosition = client.close_position_if_no_open_orders(ticker_symbol)
        canceledOrders = client.cancel_orders_if_no_position(ticker_symbol)

        if not closedPosition and not canceledOrders:
            logging.info(f"No action taken for ticker: {ticker_symbol}. No open position or orders found.")
            queue_client = create_queue_client("orders")
            encoded_message = base64.b64encode(ticker_symbol.encode("utf-8")).decode("utf-8")
            queue_client.send_message(encoded_message, visibility_timeout=60)
            logging.info(f"Re-enqueued message for ticker: {ticker_symbol}")
        else:
            logging.info(f"Processed ticker: {ticker_symbol}. Closed Position: {closedPosition}, Canceled Orders: {canceledOrders}")
        logging.info(f"Queue trigger function processed a message for ticker: {ticker_symbol}")
    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode message body for message ID {msg.id}. Error: {e}", exc_info=True)
        return
    except Exception as e:
        logging.error(f"Unexpected error while processing message ID {msg.id}. Error: {e}", exc_info=True)
        return
