import azure.functions as func
import logging
import base64
from configuration import get_env_variables
from futures_client import FuturesClient
from azure.storage.queue import QueueClient

def main(msg: func.QueueMessage):
    try:
        env_vars = get_env_variables()
        ticker_symbol_bytes = msg.get_body()
        ticker_symbol = ticker_symbol_bytes.decode('utf-8', errors='replace').strip()
        client = FuturesClient(env_vars["API_KEY"], env_vars["API_SECRET"])
        closedPosition = client.close_position_if_no_open_orders(ticker_symbol)
        canceledOrders = client.cancel_orders_if_no_position(ticker_symbol)

        if not closedPosition and not canceledOrders:
            logging.info(f"No action taken for ticker: {ticker_symbol}. No open position or orders found.")
            queue_client = QueueClient.from_connection_string(
                conn_str=env_vars["AZURE_STORAGE_CONNECTION_STRING"],
                queue_name="orders"
            )
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
