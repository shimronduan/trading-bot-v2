import logging
import azure.functions as func
import json
from trading_config import SYMBOL
from utils.client_factory import create_futures_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Testing function triggered')

    return func.HttpResponse(json.dumps({"status": "success", "message": "Message DOGEUSDT enqueued"}), status_code=200, mimetype="application/json")
