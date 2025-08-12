from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from datetime import datetime

@dataclass
class TakeProfitStopLossInfo:
    """Data class for Take Profit and Stop Loss information"""
    atr_multiple: float
    close_fraction: int
    row_key: Optional[str] = None
    partition_key: str = "tp"
    timestamp: Optional[Union[datetime, str]] = None
    
    def to_entity(self) -> Dict[str, Any]:
        """Convert to Azure Table Storage entity format"""
        entity = {
            "PartitionKey": self.partition_key,
            "RowKey": self.row_key,
            "atr_multiple": self.atr_multiple,
            "close_fraction": self.close_fraction
        }
        if self.timestamp:
            entity["Timestamp"] = self.timestamp
        return entity
    
    @classmethod
    def from_entity(cls, entity: Dict[str, Any]) -> 'TakeProfitStopLossInfo':
        """Create instance from Azure Table Storage entity"""
        import logging
        
        # Debug: Log all available keys in the entity
        logging.info(f"Entity keys: {list(entity.keys())}")
        logging.info(f"Full entity: {entity}")
        
        # Try different timestamp field names that Azure Table Storage might use
        # Note: Azure Table Storage system properties might be accessed differently
        timestamp = None
        
        # Check various possible timestamp fields
        for ts_field in ["Timestamp", "timestamp", "_ts", "last_modified", "odata.etag"]:
            if ts_field in entity:
                timestamp = entity[ts_field]
                logging.info(f"Found timestamp in field '{ts_field}': {timestamp}")
                break
        
        # If no timestamp found, try to get it from metadata or etag
        if not timestamp and hasattr(entity, 'metadata'):
            timestamp = getattr(entity, 'metadata', {}).get('timestamp')
            logging.info(f"Found timestamp in metadata: {timestamp}")
        
        # If still no timestamp, use current time as fallback
        if not timestamp:
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc)
            logging.info(f"Using current time as timestamp: {timestamp}")
        
        logging.info(f"Final timestamp value: {timestamp}, type: {type(timestamp)}")
        
        return cls(
            atr_multiple=float(entity.get("atr_multiple", 0.0)),
            close_fraction=int(entity.get("close_fraction", 0)),
            row_key=entity.get("RowKey"),
            partition_key=entity.get("PartitionKey", "tp"),
            timestamp=timestamp
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TakeProfitStopLossInfo':
        """Create instance from dictionary (e.g., from HTTP request)"""
        # Support both "id" and "RowKey" formats
        row_key = data.get("id") or data.get("RowKey")
        # Support custom PartitionKey, default to "tp"
        partition_key = data.get("PartitionKey", "tp")
        
        return cls(
            atr_multiple=float(data.get("atr_multiple", 0.0)),
            close_fraction=int(data.get("close_fraction", 0)),
            row_key=row_key,
            partition_key=partition_key
        )
    
    def validate(self) -> bool:
        """Validate the data"""
        return (
            self.atr_multiple > 0 and
            self.close_fraction > 0 and
            self.close_fraction <= 100 and
            self.row_key is not None
        )
