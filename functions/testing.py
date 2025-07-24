import azure.functions as func
import json
from configuration import get_env_variables
from trading_config import SYMBOL
from futures_client import FuturesClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    env_vars = get_env_variables()
    client = FuturesClient(env_vars["API_KEY"], env_vars["API_SECRET"])
    client.close_position_if_no_open_orders(SYMBOL)
    client.cancel_orders_if_no_position(SYMBOL)

    return func.HttpResponse(json.dumps({"status": "success", "message": "Message DOGEUSDT enqueued"}), status_code=200, mimetype="application/json")
