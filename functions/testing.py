import azure.functions as func
import json
from trading_config import SYMBOL
from utils.client_factory import create_futures_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    client = create_futures_client()
    client.close_position_if_no_open_orders(SYMBOL)
    client.cancel_orders_if_no_position(SYMBOL)

    return func.HttpResponse(json.dumps({"status": "success", "message": "Message DOGEUSDT enqueued"}), status_code=200, mimetype="application/json")
