import azure.functions as func
import json
import logging
from typing import Dict, Any
from managers.tp_sl_manager import TpSlManager
from models.tp_sl_info import TakeProfitStopLossInfo

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for Take Profit and Stop Loss CRUD operations.
    
    Endpoints:
    - GET /tp-sl - List all records
    - GET /tp-sl?partition_key=X&row_key=Y - Get specific record
    - POST /tp-sl - Create new record
    - PUT /tp-sl - Update existing record (upsert)
    - DELETE /tp-sl?partition_key=X&row_key=Y - Delete record
    """
    logging.info('TP/SL HTTP trigger function processed a request.')
    
    try:
        method = req.method.upper()
        tp_sl_manager = TpSlManager()
        
        if method == "GET":
            return handle_get_request(req, tp_sl_manager)
        elif method == "POST":
            return handle_post_request(req, tp_sl_manager)
        elif method == "PUT":
            return handle_put_request(req, tp_sl_manager)
        elif method == "DELETE":
            return handle_delete_request(req, tp_sl_manager)
        else:
            return create_error_response(f"Method {method} not allowed", 405)
            
    except Exception as e:
        logging.error(f"Unhandled error in TP/SL HTTP trigger: {e}", exc_info=True)
        return create_error_response("Internal server error", 500)

def handle_get_request(req: func.HttpRequest, tp_sl_manager: TpSlManager) -> func.HttpResponse:
    """Handle GET requests for retrieving TP/SL records."""
    try:
        partition_key = req.params.get('partition_key')
        row_key = req.params.get('row_key')
        
        if partition_key and row_key:
            # Get specific record
            tp_sl_info = tp_sl_manager.get_tp_sl(partition_key, row_key)
            if tp_sl_info:
                return create_success_response(tp_sl_info.to_dict())
            else:
                return create_error_response("Record not found", 404)
        elif partition_key:
            # Get all records for a partition
            tp_sl_list = tp_sl_manager.get_tp_sl_by_partition(partition_key)
            response_data = [tp_sl.to_dict() for tp_sl in tp_sl_list]
            return create_success_response(response_data)
        else:
            # Get all records
            tp_sl_list = tp_sl_manager.list_all_tp_sl()
            response_data = [tp_sl.to_dict() for tp_sl in tp_sl_list]
            return create_success_response(response_data)
            
    except Exception as e:
        logging.error(f"Error handling GET request: {e}")
        return create_error_response("Error retrieving records", 500)

def handle_post_request(req: func.HttpRequest, tp_sl_manager: TpSlManager) -> func.HttpResponse:
    """Handle POST requests for creating new TP/SL records."""
    try:
        request_data = get_request_json(req)
        if not request_data:
            return create_error_response("Invalid JSON in request body", 400)
        
        tp_sl_info = TakeProfitStopLossInfo.from_dict(request_data)
        success = tp_sl_manager.create_tp_sl(tp_sl_info)
        
        if success:
            return create_success_response(
                tp_sl_info.to_dict(), 
                "Record created successfully", 
                201
            )
        else:
            return create_error_response("Failed to create record", 500)
            
    except ValueError as e:
        logging.error(f"Validation error in POST request: {e}")
        return create_error_response(f"Validation error: {str(e)}", 400)
    except Exception as e:
        logging.error(f"Error handling POST request: {e}")
        return create_error_response("Error creating record", 500)

def handle_put_request(req: func.HttpRequest, tp_sl_manager: TpSlManager) -> func.HttpResponse:
    """Handle PUT requests for updating TP/SL records."""
    try:
        request_data = get_request_json(req)
        if not request_data:
            return create_error_response("Invalid JSON in request body", 400)
        
        tp_sl_info = TakeProfitStopLossInfo.from_dict(request_data)
        success = tp_sl_manager.update_tp_sl(tp_sl_info)
        
        if success:
            return create_success_response(
                tp_sl_info.to_dict(), 
                "Record updated successfully"
            )
        else:
            return create_error_response("Failed to update record", 500)
            
    except ValueError as e:
        logging.error(f"Validation error in PUT request: {e}")
        return create_error_response(f"Validation error: {str(e)}", 400)
    except Exception as e:
        logging.error(f"Error handling PUT request: {e}")
        return create_error_response("Error updating record", 500)

def handle_delete_request(req: func.HttpRequest, tp_sl_manager: TpSlManager) -> func.HttpResponse:
    """Handle DELETE requests for removing TP/SL records."""
    try:
        partition_key = req.params.get('partition_key')
        row_key = req.params.get('row_key')
        
        if not partition_key or not row_key:
            return create_error_response("partition_key and row_key parameters are required", 400)
        
        success = tp_sl_manager.delete_tp_sl(partition_key, row_key)
        
        if success:
            return create_success_response(
                {"partition_key": partition_key, "row_key": row_key}, 
                "Record deleted successfully"
            )
        else:
            return create_error_response("Failed to delete record", 500)
            
    except Exception as e:
        logging.error(f"Error handling DELETE request: {e}")
        return create_error_response("Error deleting record", 500)

def get_request_json(req: func.HttpRequest) -> Dict[str, Any]:
    """Extract and parse JSON from request body."""
    try:
        return req.get_json() or {}
    except ValueError:
        logging.error("Invalid JSON in request body")
        return {}

def create_success_response(data: Any, message: str = "Success", status_code: int = 200) -> func.HttpResponse:
    """Create a standardized success response."""
    response_body = {
        "success": True,
        "message": message,
        "data": data
    }
    return func.HttpResponse(
        json.dumps(response_body, default=str),
        status_code=status_code,
        headers={"Content-Type": "application/json"}
    )

def create_error_response(message: str, status_code: int = 400) -> func.HttpResponse:
    """Create a standardized error response."""
    response_body = {
        "success": False,
        "message": message,
        "data": None
    }
    return func.HttpResponse(
        json.dumps(response_body),
        status_code=status_code,
        headers={"Content-Type": "application/json"}
    )
