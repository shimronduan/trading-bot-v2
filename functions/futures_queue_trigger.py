import azure.functions as func
import logging
from functions.futures_handler import handle_futures
from utils.extract_body import extractMessageBody
from trading_enums import TradingEnums

def main(msg: func.QueueMessage):
    try:
        message = msg.get_json()
        body = message.get("Body", "").strip()
        logging.info(f"Queue trigger function processed a message body: {body}")
        signal_type = extractMessageBody(body)
        if TradingEnums.is_valid_signal(signal_type):
            response_message = handle_futures(signal_type)
            logging.info(f"Processed message with signal type: {signal_type} - Response: {response_message}")
        else:
            logging.error(f"Received unsupported signal type: {signal_type} in message ID {msg.id}. Skipping processing.")
    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode message body for message ID {msg.id}. Error: {e}", exc_info=True)
        return
    except Exception as e:
        logging.error(f"Unexpected error while processing message ID {msg.id}. Error: {e}", exc_info=True)
        return
