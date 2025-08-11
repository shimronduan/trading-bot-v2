import azure.functions as func
import json
from trading_config import SYMBOL
from utils.client_factory import create_futures_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    client = create_futures_client()
    pnl = client.get_pnl_over_interval(SYMBOL, interval_hours=48)

    return func.HttpResponse(json.dumps({"status": "success", "pnl": pnl}), status_code=200, mimetype="application/json")
