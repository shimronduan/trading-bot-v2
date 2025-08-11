from typing import List, Optional, Dict, Any
import logging
from azure_table_storage import AzureTableStorage
from models.tp_sl_info import TakeProfitStopLossInfo
from utils.storage_factory import create_table_storage_client

class TpSlManager:
    """
    Manager for Take Profit and Stop Loss operations using Azure Table Storage.
    """
    
    def __init__(self, table_storage_client: Optional[AzureTableStorage] = None):
        self.table_storage_client = table_storage_client or create_table_storage_client()
    
    def create_tp_sl(self, tp_sl_info: TakeProfitStopLossInfo) -> bool:
        """Create a new Take Profit and Stop Loss record."""
        try:
            entity = tp_sl_info.to_entity()
            success = self.table_storage_client.create_record(entity)
            if success:
                logging.info(f"Successfully created TP/SL record: PK={tp_sl_info.partition_key}, RK={tp_sl_info.row_key}")
            return success
        except Exception as e:
            logging.error(f"Error creating TP/SL record: {e}")
            return False
    
    def get_tp_sl(self, partition_key: str, row_key: str) -> Optional[TakeProfitStopLossInfo]:
        """Get a specific Take Profit and Stop Loss record."""
        try:
            entity = self.table_storage_client.read_record(partition_key, row_key)
            if entity:
                return TakeProfitStopLossInfo.from_entity(entity)
            return None
        except Exception as e:
            logging.error(f"Error retrieving TP/SL record (PK={partition_key}, RK={row_key}): {e}")
            return None
    
    def update_tp_sl(self, tp_sl_info: TakeProfitStopLossInfo) -> bool:
        """Update (upsert) a Take Profit and Stop Loss record."""
        try:
            entity = tp_sl_info.to_entity()
            success = self.table_storage_client.upsert_record(entity)
            if success:
                logging.info(f"Successfully updated TP/SL record: PK={tp_sl_info.partition_key}, RK={tp_sl_info.row_key}")
            return success
        except Exception as e:
            logging.error(f"Error updating TP/SL record: {e}")
            return False
    
    def delete_tp_sl(self, partition_key: str, row_key: str) -> bool:
        """Delete a Take Profit and Stop Loss record."""
        try:
            success = self.table_storage_client.delete_record(partition_key, row_key)
            if success:
                logging.info(f"Successfully deleted TP/SL record: PK={partition_key}, RK={row_key}")
            return success
        except Exception as e:
            logging.error(f"Error deleting TP/SL record (PK={partition_key}, RK={row_key}): {e}")
            return False
    
    def list_all_tp_sl(self) -> List[TakeProfitStopLossInfo]:
        """List all Take Profit and Stop Loss records."""
        try:
            entities = self.table_storage_client.list_records()
            tp_sl_list = []
            for entity in entities:
                try:
                    tp_sl_info = TakeProfitStopLossInfo.from_entity(entity)
                    tp_sl_list.append(tp_sl_info)
                except Exception as e:
                    logging.warning(f"Skipping invalid TP/SL record: {e}")
                    continue
            logging.info(f"Retrieved {len(tp_sl_list)} TP/SL records")
            return tp_sl_list
        except Exception as e:
            logging.error(f"Error listing TP/SL records: {e}")
            return []
    
    def get_tp_sl_by_partition(self, partition_key: str) -> List[TakeProfitStopLossInfo]:
        """Get all Take Profit and Stop Loss records for a specific partition."""
        try:
            all_records = self.list_all_tp_sl()
            filtered_records = [record for record in all_records if record.partition_key == partition_key]
            logging.info(f"Retrieved {len(filtered_records)} TP/SL records for partition: {partition_key}")
            return filtered_records
        except Exception as e:
            logging.error(f"Error retrieving TP/SL records for partition {partition_key}: {e}")
            return []
