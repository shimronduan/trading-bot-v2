import azure.functions as func
import json
import logging
from technical_analysis import TechnicalAnalysis
from trading_config import SYMBOL
from utils.client_factory import create_futures_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    raw_body = req.get_body()
    logging.info(f"Raw request body: {raw_body}")
    
    client = create_futures_client()

    # --- NEW: Use the TechnicalAnalysis class ---
    # Initialize it with the same client instance
    ta_calculator = TechnicalAnalysis(client=client.client)
    
    # Get the latest ATR value
    current_atr = ta_calculator.get_atr(symbol=SYMBOL)
    
    if current_atr is None:
        raise ValueError("Failed to calculate ATR, cannot proceed with trade.")
            

    return func.HttpResponse(json.dumps({"status": "success", "message": f"Message DOGEUSDT {current_atr}"}), status_code=200, mimetype="application/json")
