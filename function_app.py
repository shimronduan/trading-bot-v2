import azure.functions as func
import logging
from decimal import Decimal, getcontext
import json
import os
from azure_table_storage import AzureTableStorage
from configuration import get_env_variables
from trading_config import SYMBOL
import base64
from futures_client import FuturesClient
from azure.storage.queue import QueueClient


getcontext().prec = 18 # Decimal precision

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    
@app.route(route="futures") # New route name for clarity
def futures_trading(req: func.HttpRequest) -> func.HttpResponse:

    env_vars = get_env_variables()
    client = FuturesClient(env_vars["API_KEY"], env_vars["API_SECRET"])
    try:
        raw_body = req.get_body()
        logging.info(f"Raw request body: {raw_body}")
        signal_type = raw_body.decode('utf-8').title().strip()
        
        response_message = ""
        if signal_type == "Close":
            # This calls your new method to close everything
            response_message = client.close_all_for_symbol(symbol=SYMBOL)
        else:    
            # signal_type = client.parse_and_validate_request(req)
            desired_side = 'BUY' if signal_type == 'Long' else 'SELL'

            # 2. Manage any existing positions (close if opposite, ignore if same)
            should_proceed = client.manage_existing_position(signal_type)

            if not should_proceed:
                return func.HttpResponse(json.dumps({"status": "ignored", "message": f"Signal {signal_type} ignored due to existing position."}), status_code=200)

            # 3. Calculate the correct order quantity
            quantity = client.calculate_trade_quantity()

            ats_client = AzureTableStorage(connection_string=env_vars["AZURE_STORAGE_CONNECTION_STRING"], table_name=env_vars["TP_SL_TABLE_NAME"])

            records = ats_client.list_records()
            # 4. Execute the full trade with SL and TP
            response_message = client.execute_trade_with_sl_tp(desired_side, quantity,records)
            
            try:
                queue_client = QueueClient.from_connection_string(
                    conn_str=env_vars["AZURE_STORAGE_CONNECTION_STRING"],
                    queue_name="orders" 
                )
                # Encode the message 'DOGEUSDT' in Base64
                encoded_message = base64.b64encode("DOGEUSDT".encode("utf-8")).decode("utf-8")
                queue_client.send_message(encoded_message, visibility_timeout=60) 
                logging.info("Successfully enqueued message: DOGEUSDT")
            except Exception as e:
                logging.error(f"Failed to enqueue message. Error: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "success", "message": response_message}), status_code=200)

    except ValueError as e:
        # Catches validation errors from parse_and_validate_request
        logging.warning(str(e))
        return func.HttpResponse(json.dumps({"status": "ignored", "message": str(e)}), status_code=200)
    except Exception as e:
        # Catches any other unexpected errors (e.g., calculation errors)
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": str(e)}), status_code=500)
    
@app.route(route="testing") # New route name for clarity
def testing(req: func.HttpRequest) -> func.HttpResponse:
    env_vars = get_env_variables()
    client = FuturesClient(env_vars["API_KEY"], env_vars["API_SECRET"])
    client.close_position_if_no_open_orders(SYMBOL)
    client.cancel_orders_if_no_position(SYMBOL)
    # try:
    #     queue_client = QueueClient.from_connection_string(
    #         conn_str=AZURE_STORAGE_CONNECTION_STRING,
    #         queue_name="orders" 
    #     )
    #     # Encode the message 'DOGEUSDT' in Base64
    #     encoded_message = base64.b64encode("DOGEUSDT".encode("utf-8")).decode("utf-8")
    #     queue_client.send_message(encoded_message)
    #     logging.info("Successfully enqueued message: DOGEUSDT")
    # except Exception as e:
    #     logging.error(f"Failed to enqueue message. Error: {e}", exc_info=True)
    #     return func.HttpResponse(json.dumps({"status": "error", "message": str(e)}), status_code=500, mimetype="application/json")

    return func.HttpResponse(json.dumps({"status": "success", "message": "Message DOGEUSDT enqueued"}), status_code=200, mimetype="application/json")

@app.function_name(name="QueueTriggerFunction")
@app.queue_trigger(arg_name="msg", queue_name="orders", connection="AZURE_STORAGE_CONNECTION_STRING")
def queue_trigger_function(msg: func.QueueMessage):
    try:
        env_vars = get_env_variables()
        # Decode the message body from bytes, replacing any invalid characters.
        ticker_symbol_bytes = msg.get_body()
        ticker_symbol = ticker_symbol_bytes.decode('utf-8', errors='replace').strip()
        client = FuturesClient(env_vars["API_KEY"], env_vars["API_SECRET"])
        closedPosition = client.close_position_if_no_open_orders(ticker_symbol)
        canceledOrders = client.cancel_orders_if_no_position(ticker_symbol)
        if not closedPosition and not canceledOrders:
            logging.info(f"No action taken for ticker: {ticker_symbol}. No open position or orders found.")
            # Re-enqueue the message
            from azure.storage.queue import QueueClient
            queue_client = QueueClient.from_connection_string(
                conn_str=env_vars["AZURE_STORAGE_CONNECTION_STRING"],
                queue_name="orders"
            )
            # Re-encode the message as base64 if needed
            import base64
            encoded_message = base64.b64encode(ticker_symbol.encode("utf-8")).decode("utf-8")
            queue_client.send_message(encoded_message, visibility_timeout=60)
            logging.info(f"Re-enqueued message for ticker: {ticker_symbol}")
        else:
            logging.info(f"Processed ticker: {ticker_symbol}. Closed Position: {closedPosition}, Canceled Orders: {canceledOrders}")
        logging.info(f"Queue trigger function processed a message for ticker: {ticker_symbol}")
    except UnicodeDecodeError as e:
        logging.error(f"Failed to decode message body for message ID {msg.id}. Error: {e}", exc_info=True)
        return
    except Exception as e:
        logging.error(f"Unexpected error while processing message ID {msg.id}. Error: {e}", exc_info=True)
        return