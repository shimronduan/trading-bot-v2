import azure.functions as func
import logging
import json
from functions.futures_handler import handle_futures
from utils.extract_body import extractMessageBody
from trading_enums import TradingEnums

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        raw_body = req.get_body()
        decoded_body = raw_body.decode('utf-8').strip()
        signal_type = extractMessageBody(decoded_body)
        if TradingEnums.is_valid_signal(signal_type):
            response_message = handle_futures(signal_type)
            return func.HttpResponse(json.dumps({"status": "success", "message": response_message}), status_code=200)
        else:
            logging.error(f"Received unsupported signal type: {signal_type}. Skipping processing.")
            return func.HttpResponse(json.dumps({"status": "ignored", "message": f"Unsupported signal type: {signal_type}"}), status_code=200)

    except ValueError as e:
        logging.warning(str(e))
        return func.HttpResponse(json.dumps({"status": "ignored", "message": str(e)}), status_code=200)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": str(e)}), status_code=500)
