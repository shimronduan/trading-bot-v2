import azure.functions as func
from functions.http_trigger import main as http_trigger
from functions.futures_http_trigger import main as futures_trading
from functions.testing import main as testing
from functions.queue_trigger import main as queue_trigger_function
from functions.futures_queue_trigger import main as futures_queue_trigger
from functions.tp_sl_http_trigger import main as tp_sl_http_trigger

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger")
def http_trigger_route(req: func.HttpRequest):
    return http_trigger(req)

@app.route(route="futures")
def futures_trading_route(req: func.HttpRequest):
    return futures_trading(req)

@app.function_name(name="FuturesQueueTriggerFunction")
@app.queue_trigger(arg_name="msg", queue_name="futures", connection="AZURE_STORAGE_CONNECTION_STRING")
def futures_queue_trigger_function_route(msg: func.QueueMessage):
    return futures_queue_trigger(msg)

@app.route(route="testing")
def testing_route(req: func.HttpRequest):
    return testing(req)

@app.function_name(name="QueueTriggerFunction")
@app.queue_trigger(arg_name="msg", queue_name="orders", connection="AZURE_STORAGE_CONNECTION_STRING")
def queue_trigger_function_route(msg: func.QueueMessage):
    return queue_trigger_function(msg)

# Take Profit/Stop Loss CRUD endpoints
@app.route(route="tp_sl", methods=["GET", "POST"])
def tp_sl_route(req: func.HttpRequest):
    return tp_sl_http_trigger(req)

@app.route(route="tp_sl/{id}", methods=["GET", "PUT", "DELETE"])
def tp_sl_with_id_route(req: func.HttpRequest):
    return tp_sl_http_trigger(req)