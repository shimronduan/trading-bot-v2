import azure.functions as func
import json
from trading_config import SYMBOL
from utils.client_factory import create_futures_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    client = create_futures_client()
    pnl = client.get_current_pnl()

    return func.HttpResponse(json.dumps({"status": "success", "message": pnl}), status_code=200, mimetype="application/json")
