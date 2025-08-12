import azure.functions as func
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from azure_table_storage import AzureTableStorage
from models.tp_sl_info import TakeProfitStopLossInfo

def format_timestamp(timestamp) -> Optional[str]:
    """Helper function to format timestamp properly"""
    if not timestamp:
        return None
    if isinstance(timestamp, datetime):
        return timestamp.isoformat() + "Z"
    return str(timestamp)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for Take Profit and Stop Loss CRUD operations
    Endpoints:
    - GET /tp_sl/{id} - Get specific record
    - GET /tp_sl - Get all records
    - POST /tp_sl - Create new record
    - PUT /tp_sl/{id} - Update existing record
    - DELETE /tp_sl/{id} - Delete record
    """
    logging.info('Take Profit/Stop Loss HTTP trigger function processed a request.')
    
    try:
        # Initialize Azure Table Storage
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            return func.HttpResponse(
                json.dumps({"error": "Azure Storage connection string not configured"}),
                status_code=500,
                mimetype="application/json"
            )
        
        table_storage = AzureTableStorage(connection_string, "TakeProfitAndStopLoss")
        
        # Get HTTP method and route parameters
        method = req.method
        route_params = req.route_params
        record_id = route_params.get('id') if route_params else None
        
        if method == "GET":
            if record_id:
                # Get specific record
                return get_record(table_storage, record_id)
            else:
                # Get all records
                return get_all_records(table_storage)
        
        elif method == "POST":
            # Create new record
            return create_record(req, table_storage)
        
        elif method == "PUT":
            if not record_id:
                return func.HttpResponse(
                    json.dumps({"error": "Record ID required for update"}),
                    status_code=400,
                    mimetype="application/json"
                )
            # Update existing record
            return update_record(req, table_storage, record_id)
        
        elif method == "DELETE":
            if not record_id:
                return func.HttpResponse(
                    json.dumps({"error": "Record ID required for deletion"}),
                    status_code=400,
                    mimetype="application/json"
                )
            # Delete record - pass the request to handle partition key from body
            return delete_record(req, table_storage, record_id)
        
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Method {method} not allowed"}),
                status_code=405,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"Error in tp_sl HTTP trigger: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def get_record(table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Get a specific record by ID"""
    try:
        entity = table_storage.read_record("tp", record_id)
        if entity:
            tp_sl_info = TakeProfitStopLossInfo.from_entity(entity)
            return func.HttpResponse(
                json.dumps({
                    "PartitionKey": tp_sl_info.partition_key,
                    "RowKey": tp_sl_info.row_key,
                    "atr_multiple": tp_sl_info.atr_multiple,
                    "close_fraction": tp_sl_info.close_fraction,
                    "Timestamp": format_timestamp(tp_sl_info.timestamp)
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Record with ID {record_id} not found"}),
                status_code=404,
                mimetype="application/json"
            )
    except Exception as e:
        logging.error(f"Error getting record {record_id}: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve record"}),
            status_code=500,
            mimetype="application/json"
        )

def get_all_records(table_storage: AzureTableStorage) -> func.HttpResponse:
    """Get all records"""
    try:
        entities = table_storage.list_records()
        records = []
        for entity in entities:
            tp_sl_info = TakeProfitStopLossInfo.from_entity(entity)
            records.append({
                "PartitionKey": tp_sl_info.partition_key,
                "RowKey": tp_sl_info.row_key,
                "atr_multiple": tp_sl_info.atr_multiple,
                "close_fraction": tp_sl_info.close_fraction,
                "Timestamp": format_timestamp(tp_sl_info.timestamp)
            })
        
        return func.HttpResponse(
            json.dumps({"records": records, "count": len(records)}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error getting all records: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve records"}),
            status_code=500,
            mimetype="application/json"
        )

def create_record(req: func.HttpRequest, table_storage: AzureTableStorage) -> func.HttpResponse:
    """Create a new record"""
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Extract ID from request body - support both "id" and "RowKey" formats
        record_id = req_body.get("id") or req_body.get("RowKey")
        if not record_id:
            return func.HttpResponse(
                json.dumps({"error": "ID or RowKey is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Ensure the request body has the id field for the model
        req_body["id"] = record_id
        
        # Create TakeProfitStopLossInfo instance
        tp_sl_info = TakeProfitStopLossInfo.from_dict(req_body)
        
        # Validate data
        if not tp_sl_info.validate():
            return func.HttpResponse(
                json.dumps({"error": "Invalid data. atr_multiple must be > 0, close_fraction must be between 1-100"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Check if record already exists
        existing = table_storage.read_record(tp_sl_info.partition_key, record_id)
        if existing:
            return func.HttpResponse(
                json.dumps({"error": f"Record with ID {record_id} already exists"}),
                status_code=409,
                mimetype="application/json"
            )
        
        # Create record
        entity = tp_sl_info.to_entity()
        success = table_storage.create_record(entity)
        
        if success:
            return func.HttpResponse(
                json.dumps({
                    "message": "Record created successfully",
                    "PartitionKey": tp_sl_info.partition_key,
                    "RowKey": record_id,
                    "atr_multiple": tp_sl_info.atr_multiple,
                    "close_fraction": tp_sl_info.close_fraction
                }),
                status_code=201,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Failed to create record"}),
                status_code=500,
                mimetype="application/json"
            )
    
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid request data: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error creating record: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to create record"}),
            status_code=500,
            mimetype="application/json"
        )

def update_record(req: func.HttpRequest, table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Update an existing record"""
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Set the ID from the URL parameter
        req_body["id"] = record_id
        
        # Create TakeProfitStopLossInfo instance
        tp_sl_info = TakeProfitStopLossInfo.from_dict(req_body)
        
        # Validate data
        if not tp_sl_info.validate():
            return func.HttpResponse(
                json.dumps({"error": "Invalid data. atr_multiple must be > 0, close_fraction must be between 1-100"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Update record using upsert (will create if doesn't exist)
        entity = tp_sl_info.to_entity()
        success = table_storage.upsert_record(entity)
        
        if success:
            return func.HttpResponse(
                json.dumps({
                    "message": "Record updated successfully",
                    "PartitionKey": tp_sl_info.partition_key,
                    "RowKey": record_id,
                    "atr_multiple": tp_sl_info.atr_multiple,
                    "close_fraction": tp_sl_info.close_fraction
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Failed to update record"}),
                status_code=500,
                mimetype="application/json"
            )
    
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid request data: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error updating record {record_id}: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to update record"}),
            status_code=500,
            mimetype="application/json"
        )

def delete_record(req: func.HttpRequest, table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Delete a record"""
    try:
        # Try to get partition key from request body
        partition_key = "tp"  # default
        try:
            req_body = req.get_json()
            if req_body and "PartitionKey" in req_body:
                partition_key = req_body["PartitionKey"]
                logging.info(f"Using partition key from request body: {partition_key}")
        except:
            logging.info("No request body or PartitionKey found, using default 'tp'")
        
        # First try to find the record with the specified partition key
        existing = table_storage.read_record(partition_key, record_id)
        
        # If not found with specified partition key, search all partitions
        if not existing:
            logging.info(f"Record not found with PartitionKey '{partition_key}', searching all records...")
            all_entities = table_storage.list_records()
            for ent in all_entities:
                if ent.get("RowKey") == record_id:
                    existing = ent
                    partition_key = ent.get("PartitionKey", "tp")
                    logging.info(f"Found record with PartitionKey: {partition_key}")
                    break
        
        if not existing:
            return func.HttpResponse(
                json.dumps({"error": f"Record with ID {record_id} not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Delete record using the correct partition key
        success = table_storage.delete_record(partition_key, record_id)
        
        if success:
            return func.HttpResponse(
                json.dumps({"message": f"Record with ID {record_id} deleted successfully"}),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Failed to delete record"}),
                status_code=500,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"Error deleting record {record_id}: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to delete record"}),
            status_code=500,
            mimetype="application/json"
        )
