import azure.functions as func
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from azure_table_storage import AzureTableStorage
from models.trading_config_info import TradingConfigInfo

def format_timestamp(timestamp) -> Optional[str]:
    """Helper function to format timestamp properly"""
    if not timestamp:
        return None
    if isinstance(timestamp, datetime):
        return timestamp.isoformat() + "Z"
    return str(timestamp)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for Trading Config CRUD operations
    Endpoints:
    - GET /trading_config/{id} - Get specific record
    - GET /trading_config - Get all records
    - POST /trading_config - Create new record
    - PUT /trading_config/{id} - Update existing record
    - DELETE /trading_config/{id} - Delete record
    """
    logging.info('Trading Config HTTP trigger function processed a request.')
    
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
        logging.error(f"Error in trading config HTTP trigger: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def get_record(table_storage: AzureTableStorage, record_id: str) -> func.HttpResponse:
    """Get a specific record by ID"""
    try:
        # Try with record_id as both partition key and row key (common pattern for trading symbols)
        entity = table_storage.read_record(record_id, record_id)
        
        # If not found, search all records
        if not entity:
            all_entities = table_storage.list_records()
            for ent in all_entities:
                if ent.get("RowKey") == record_id:
                    entity = ent
                    break
        
        if entity:
            config_info = TradingConfigInfo.from_entity(entity)
            return func.HttpResponse(
                json.dumps({
                    "PartitionKey": config_info.partition_key,
                    "RowKey": config_info.row_key,
                    "LEVERAGE": config_info.leverage,
                    "WALLET_ALLOCATION": config_info.wallet_allocation,
                    "Timestamp": format_timestamp(config_info.timestamp)
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
            config_info = TradingConfigInfo.from_entity(entity)
            records.append({
                "PartitionKey": config_info.partition_key,
                "RowKey": config_info.row_key,
                "LEVERAGE": config_info.leverage,
                "WALLET_ALLOCATION": config_info.wallet_allocation,
                "Timestamp": format_timestamp(config_info.timestamp)
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
        
        # Create TradingConfigInfo instance
        config_info = TradingConfigInfo.from_dict(req_body)
        
        # Validate data
        if not config_info.validate():
            return func.HttpResponse(
                json.dumps({"error": "Invalid data. leverage must be > 0, wallet_allocation must be between 0-1.0"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Check if record already exists
        existing = table_storage.read_record(config_info.partition_key or record_id, record_id)
        if existing:
            return func.HttpResponse(
                json.dumps({"error": f"Record with ID {record_id} already exists"}),
                status_code=409,
                mimetype="application/json"
            )
        
        # Create record
        entity = config_info.to_entity()
        success = table_storage.create_record(entity)
        
        if success:
            return func.HttpResponse(
                json.dumps({
                    "message": "Record created successfully",
                    "PartitionKey": config_info.partition_key,
                    "RowKey": record_id,
                    "LEVERAGE": config_info.leverage,
                    "WALLET_ALLOCATION": config_info.wallet_allocation
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
        
        # Create TradingConfigInfo instance
        config_info = TradingConfigInfo.from_dict(req_body)
        
        # Validate data
        if not config_info.validate():
            return func.HttpResponse(
                json.dumps({"error": "Invalid data. leverage must be > 0, wallet_allocation must be between 0-1.0"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Update record using upsert (will create if doesn't exist)
        entity = config_info.to_entity()
        success = table_storage.upsert_record(entity)
        
        if success:
            return func.HttpResponse(
                json.dumps({
                    "message": "Record updated successfully",
                    "PartitionKey": config_info.partition_key,
                    "RowKey": record_id,
                    "LEVERAGE": config_info.leverage,
                    "WALLET_ALLOCATION": config_info.wallet_allocation
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
        partition_key = record_id  # default to record_id as partition key
        try:
            req_body = req.get_json()
            if req_body and "PartitionKey" in req_body:
                partition_key = req_body["PartitionKey"]
                logging.info(f"Using partition key from request body: {partition_key}")
        except:
            logging.info(f"No request body or PartitionKey found, using default '{record_id}'")
        
        # First try to find the record with the specified partition key
        existing = table_storage.read_record(partition_key, record_id)
        
        # If not found with specified partition key, search all partitions
        if not existing:
            logging.info(f"Record not found with PartitionKey '{partition_key}', searching all records...")
            all_entities = table_storage.list_records()
            for ent in all_entities:
                if ent.get("RowKey") == record_id:
                    existing = ent
                    partition_key = ent.get("PartitionKey", record_id)
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
