import azure.functions as func
import logging
import json
import base64
from trading_config import SYMBOL
from utils.client_factory import create_futures_client
from utils.storage_factory import create_table_storage_client, create_queue_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    client = create_futures_client()
    ats_client = create_table_storage_client()
    try:
        raw_body = req.get_body()
        logging.info(f"Raw request body: {raw_body}")
        signal_type = raw_body.decode('utf-8').title().strip()

        response_message = ""
        if signal_type == "Close":
            response_message = client.close_all_for_symbol(symbol=SYMBOL)
        else:
            desired_side = 'BUY' if signal_type == 'Long' else 'SELL'
            should_proceed = client.manage_existing_position(signal_type)

            if not should_proceed:
                return func.HttpResponse(json.dumps({"status": "ignored", "message": f"Signal {signal_type} ignored due to existing position."}), status_code=200)

            quantity = client.calculate_trade_quantity()
            records = ats_client.list_records()
            response_message = client.execute_trade_with_sl_tp(desired_side, quantity, records)

            try:
                queue_client = create_queue_client(queue_name="orders")
                encoded_message = base64.b64encode("DOGEUSDT".encode("utf-8")).decode("utf-8")
                queue_client.send_message(encoded_message, visibility_timeout=60)
                logging.info("Successfully enqueued message: DOGEUSDT")
            except Exception as e:
                logging.error(f"Failed to enqueue message. Error: {e}", exc_info=True)

        return func.HttpResponse(json.dumps({"status": "success", "message": response_message}), status_code=200)

    except ValueError as e:
        logging.warning(str(e))
        return func.HttpResponse(json.dumps({"status": "ignored", "message": str(e)}), status_code=200)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": str(e)}), status_code=500)
