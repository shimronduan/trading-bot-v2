import azure.functions as func
import json
from trading_config import SYMBOL
from utils.client_factory import create_futures_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    raw_body = req.get_body()
    body = json.loads(raw_body)
    type = body.get("type", "").title().strip()
    atr = float(body.get("atr", "0.0"))
    # client = create_futures_client()
    # client.close_position_if_no_open_orders(SYMBOL)
    # client.cancel_orders_if_no_position(SYMBOL)

    return func.HttpResponse(json.dumps({"status": "success", "message": "Message DOGEUSDT enqueued"}), status_code=200, mimetype="application/json")
