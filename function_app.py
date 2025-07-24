import azure.functions as func
from functions.http_trigger import main as http_trigger
from functions.futures_trading import main as futures_trading
from functions.testing import main as testing
from functions.queue_trigger import main as queue_trigger_function

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger")
def http_trigger_route(req: func.HttpRequest):
    return http_trigger(req)

@app.route(route="futures")
def futures_trading_route(req: func.HttpRequest):
    return futures_trading(req)

@app.route(route="testing")
def testing_route(req: func.HttpRequest):
    return testing(req)

@app.function_name(name="QueueTriggerFunction")
@app.queue_trigger(arg_name="msg", queue_name="orders", connection="AZURE_STORAGE_CONNECTION_STRING")
def queue_trigger_function_route(msg: func.QueueMessage):
    return queue_trigger_function(msg)