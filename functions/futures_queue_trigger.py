import azure.functions as func
import logging
import base64
from functions.futures_handler import handle_futures
from utils.client_factory import create_futures_client
from azure.storage.queue import QueueClient

from utils.extract_body import extractMessageBody
from utils.storage_factory import create_queue_client

def main(msg: func.QueueMessage):
    try:
        message = msg.get_json()
        body = message.get("Body", "").strip()
        logging.info(f"Queue trigger function processed a message for ticker: {body}")
        signal_type, ticker, price, atr = extractMessageBody(body)
        response_message = handle_futures(signal_type, ticker, price, atr)
        logging.info(f"Processed message with signal type: {signal_type}, ticker: {ticker}, price: {price}, ATR: {atr} - Response: {response_message}")
    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode message body for message ID {msg.id}. Error: {e}", exc_info=True)
        return
    except Exception as e:
        logging.error(f"Unexpected error while processing message ID {msg.id}. Error: {e}", exc_info=True)
        return
