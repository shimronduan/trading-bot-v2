# functions/trading_config_http_trigger.py

import azure.functions as func
import json
import logging
import os
from typing import Any, Dict
from datetime import datetime
from azure_table_storage import AzureTableStorage
from models.trading_config_info import TradingConfigInfo

def json_serial(obj: Any) -> str:
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Handle TablesEntityDatetime
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for Trading Configs CRUD operations
    Endpoints:
    - GET /trading_configs/{id} - Get specific record
    - GET /trading_configs - Get all records
    - POST /trading_configs - Create new record
    - PUT /trading_configs/{id} - Update existing record
    - DELETE /trading_configs/{id} - Delete record
    """
    logging.info('Trading Configs HTTP trigger function processed a request.')
    
    try:
        # Initialize Azure Table Storage
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            return func.HttpResponse(
                json.dumps({"error": "Azure Storage connection string not configured"}),
                status_code=500,
                mimetype="application/json"
            )
        
        table_storage = AzureTableStorage(connection_string, "TradingConfigs")
        
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
        logging.error(f"Error in trading_configs HTTP trigger: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def get_record(table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Get a specific record by ID"""
    try:
        entity = table_storage.read_record(record_id, record_id)
        if entity:
            return func.HttpResponse(
                json.dumps(entity, default=json_serial),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Record not found"}),
                status_code=404,
                mimetype="application/json"
            )
    except Exception as e:
        logging.error(f"Error getting record: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def get_all_records(table_storage: AzureTableStorage) -> func.HttpResponse:
    """Get all records"""
    try:
        entities = table_storage.list_records()
        return func.HttpResponse(
            json.dumps(list(entities), default=json_serial),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error getting all records: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def create_record(req: func.HttpRequest, table_storage: AzureTableStorage) -> func.HttpResponse:
    """Create a new record"""
    try:
        body = req.get_json()
        
        # Basic validation
        required_fields = ["PartitionKey", "RowKey", "leverage", "wallet_allocation", "chart_time_interval", "atr_candles"]
        if not all(field in body for field in required_fields):
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields"}),
                status_code=400,
                mimetype="application/json"
            )
            
        trading_config: Dict[str, Any] = {
            "PartitionKey": body["PartitionKey"],
            "RowKey": body["RowKey"],
            "leverage": body["leverage"],
            "wallet_allocation": body["wallet_allocation"],
            "chart_time_interval": body["chart_time_interval"],
            "atr_candles": body["atr_candles"]
        }
        
        table_storage.create_record(trading_config)
        
        return func.HttpResponse(
            json.dumps(trading_config, default=json_serial),
            status_code=201,
            mimetype="application/json"
        )
    except ValueError as ve:
        return func.HttpResponse(
            json.dumps({"error": str(ve)}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error creating record: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def update_record(req: func.HttpRequest, table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Update an existing record"""
    try:
        body = req.get_json()
        
        partition_key = body.get("PartitionKey")
        if not partition_key:
            return func.HttpResponse(
                json.dumps({"error": "PartitionKey is required in the body for an update"}),
                status_code=400,
                mimetype="application/json"
            )

        # Check if record exists
        existing_entity = table_storage.read_record(partition_key, record_id)
        if not existing_entity:
            return func.HttpResponse(
                json.dumps({"error": "Record not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Update fields
        existing_entity["leverage"] = body.get("leverage", existing_entity.get("leverage"))
        existing_entity["wallet_allocation"] = body.get("wallet_allocation", existing_entity.get("wallet_allocation"))
        existing_entity["chart_time_interval"] = body.get("chart_time_interval", existing_entity.get("chart_time_interval"))
        existing_entity["atr_candles"] = body.get("atr_candles", existing_entity.get("atr_candles"))

        table_storage.upsert_record(existing_entity)
        
        return func.HttpResponse(
            json.dumps(existing_entity, default=json_serial),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error updating record: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def delete_record(req: func.HttpRequest, table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Delete a record"""
    try:
        if not record_id:
            return func.HttpResponse(
                json.dumps({"error": "Record ID is required in the body for deletion"}),
                status_code=400,
                mimetype="application/json"
            )
            
        table_storage.delete_record(record_id, record_id)
        
        return func.HttpResponse(
            status_code=204
        )
    except Exception as e:
        logging.error(f"Error deleting record: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


