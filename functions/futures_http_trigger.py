import azure.functions as func
import logging
import json
import base64
from functions.futures_handler import handle_futures
from trading_config import SYMBOL
from utils.client_factory import create_futures_client
from utils.extract_body import extractMessageBody
from utils.storage_factory import create_table_storage_client, create_queue_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    
    try:
        raw_body = req.get_body()
        decoded_body = raw_body.decode('utf-8').strip()
        signal_type, ticker, price, atr = extractMessageBody(decoded_body)
        response_message = handle_futures(signal_type, ticker, price, atr)
        return func.HttpResponse(json.dumps({"status": "success", "message": response_message}), status_code=200)

    except ValueError as e:
        logging.warning(str(e))
        return func.HttpResponse(json.dumps({"status": "ignored", "message": str(e)}), status_code=200)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": str(e)}), status_code=500)
