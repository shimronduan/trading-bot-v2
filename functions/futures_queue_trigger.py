import azure.functions as func
import logging
from functions.futures_handler import handle_futures
from utils.extract_body import extractMessageBody

def main(msg: func.QueueMessage):
    try:
        message = msg.get_json()
        body = message.get("Body", "").strip()
        logging.info(f"Queue trigger function processed a message for ticker: {body}")
        signal_type = extractMessageBody(body)
        response_message = handle_futures(signal_type)
        logging.info(f"Processed message with signal type: {signal_type} - Response: {response_message}")
    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode message body for message ID {msg.id}. Error: {e}", exc_info=True)
        return
    except Exception as e:
        logging.error(f"Unexpected error while processing message ID {msg.id}. Error: {e}", exc_info=True)
        return
