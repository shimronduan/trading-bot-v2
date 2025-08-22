import azure.functions as func
import json
from trading_config import SYMBOL, TRADING_CONFIGS_TABLE_NAME
from utils.client_factory import create_futures_client
from utils.storage_factory import create_table_storage_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    configs_tbl_client = create_table_storage_client(TRADING_CONFIGS_TABLE_NAME)
    configs = configs_tbl_client.read_record(SYMBOL, SYMBOL)
    if configs is not None:
        w = configs["wallet_allocation"] # Example modification, adjust as needed
        return func.HttpResponse(
            json.dumps({"status": "error", "message": w}),
            status_code=404,
            mimetype="application/json"
        )
    return func.HttpResponse(json.dumps({"status": "success", "message": "Message DOGEUSDT enqueued"}), status_code=200, mimetype="application/json")
