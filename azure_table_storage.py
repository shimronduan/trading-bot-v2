from azure.data.tables import TableServiceClient, UpdateMode
import logging
from typing import Optional, Dict, Any

class AzureTableStorage:
    """
    Handles CRUD operations for Azure Table Storage.
    """
    def __init__(self, connection_string: str, table_name: str):
        if not connection_string:
            logging.error("Azure Storage Connection string is not configured.")
            raise ValueError("Azure Storage Connection string is required.")
        self.connection_string = connection_string
        self.table_name = table_name
        self.table_service_client = TableServiceClient.from_connection_string(self.connection_string)
        try:
            self.table_service_client.create_table_if_not_exists(table_name=self.table_name)
            logging.info(f"Table '{self.table_name}' ensured to exist.")
        except Exception as e:
            logging.error(f"Error ensuring table '{self.table_name}' exists: {e}")
        self.table_client = self.table_service_client.get_table_client(table_name=self.table_name)

    def create_record(self, entity: Dict[str, Any]) -> bool:
        try:
            self.table_client.create_entity(entity=entity)
            logging.info(f"Record created in {self.table_name}: PK={entity.get('PartitionKey')}, RK={entity.get('RowKey')}")
            return True
        except Exception as e:
            logging.error(f"Error creating record in {self.table_name} (PK={entity.get('PartitionKey')}, RK={entity.get('RowKey')}): {e}")
            return False

    def read_record(self, partition_key: str, row_key: str) -> Optional[Dict[str, Any]]:
        try:
            entity = self.table_client.get_entity(partition_key=partition_key, row_key=row_key)
            logging.info(f"Record retrieved from {self.table_name}: PK={partition_key}, RK={row_key}")
            
            # Convert entity to dictionary and ensure timestamp is included
            if entity:
                entity_dict = dict(entity)
                
                # Azure Table Storage entities have metadata that includes timestamp
                if hasattr(entity, 'metadata'):
                    logging.info(f"Entity metadata: {entity.metadata}")
                    if 'timestamp' in entity.metadata:
                        entity_dict['Timestamp'] = entity.metadata['timestamp']
                
                # Log the entity type and available attributes for debugging
                logging.info(f"Entity type: {type(entity)}")
                logging.info(f"Entity dir: {[attr for attr in dir(entity) if not attr.startswith('_')]}")
                
                return entity_dict
            return entity
        except Exception as e:
            logging.info(f"Record not found in {self.table_name} (PK={partition_key}, RK={row_key}): {e}")
            return None

    def upsert_record(self, entity: Dict[str, Any]) -> bool:
        try:
            self.table_client.upsert_entity(entity=entity, mode=UpdateMode.MERGE)
            logging.info(f"Record upserted in {self.table_name}: PK={entity.get('PartitionKey')}, RK={entity.get('RowKey')}")
            return True
        except Exception as e:
            logging.error(f"Error upserting record in {self.table_name} (PK={entity.get('PartitionKey')}, RK={entity.get('RowKey')}): {e}")
            return False

    def delete_record(self, partition_key: str, row_key: str) -> bool:
        try:
            self.table_client.delete_entity(partition_key=partition_key, row_key=row_key)
            logging.info(f"Record deleted from {self.table_name}: PK={partition_key}, RK={row_key}")
            return True
        except Exception:
            logging.info(f"Record not found for deletion in {self.table_name} (PK={partition_key}, RK={row_key}). Assuming success if not found.")
            return True
        
    def list_records(self) -> list:
        try:
            entities = self.table_client.list_entities()
            records = []
            for entity in entities:
                # Convert entity to dictionary and ensure timestamp is included
                entity_dict = dict(entity)
                
                # Azure Table Storage entities have metadata that includes timestamp
                if hasattr(entity, 'metadata'):
                    logging.info(f"List entity metadata: {entity.metadata}")
                    if 'timestamp' in entity.metadata:
                        entity_dict['Timestamp'] = entity.metadata['timestamp']
                
                records.append(entity_dict)
            return records
        except Exception as e:
            logging.error(f"Error listing records from {self.table_name}: {e}")
            return []
