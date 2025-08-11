from typing import Dict, Any, Optional
import logging

class TakeProfitStopLossInfo:
    """
    Model for Take Profit and Stop Loss configuration data.
    """
    
    def __init__(self, partition_key: str, row_key: str, atr_multiple: float, close_fraction: int, timestamp: Optional[str] = None):
        self.partition_key = partition_key
        self.row_key = row_key
        self.atr_multiple = atr_multiple
        self.close_fraction = close_fraction
        self.timestamp = timestamp
    
    def to_entity(self) -> Dict[str, Any]:
        """Convert to Azure Table Storage entity format."""
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
        """Create instance from Azure Table Storage entity."""
        return cls(
            partition_key=str(entity.get("PartitionKey", "")),
            row_key=str(entity.get("RowKey", "")),
            atr_multiple=float(entity.get("atr_multiple", 0)),
            close_fraction=int(entity.get("close_fraction", 0)),
            timestamp=str(entity.get("Timestamp")) if entity.get("Timestamp") else None
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TakeProfitStopLossInfo':
        """Create instance from dictionary (e.g., HTTP request body)."""
        if not cls.validate_data(data):
            raise ValueError("Invalid data provided for TakeProfitStopLossInfo")
        
        partition_key = data.get("partition_key") or data.get("PartitionKey")
        row_key = data.get("row_key") or data.get("RowKey")
        atr_multiple = data.get("atr_multiple")
        close_fraction = data.get("close_fraction")
        timestamp = data.get("timestamp") or data.get("Timestamp")
        
        return cls(
            partition_key=str(partition_key),
            row_key=str(row_key),
            atr_multiple=float(atr_multiple) if atr_multiple is not None else 0.0,
            close_fraction=int(close_fraction) if close_fraction is not None else 0,
            timestamp=str(timestamp) if timestamp else None
        )
    
    @staticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """Validate required fields and data types."""
        try:
            # Check required fields
            partition_key = data.get("partition_key") or data.get("PartitionKey")
            row_key = data.get("row_key") or data.get("RowKey")
            atr_multiple = data.get("atr_multiple")
            close_fraction = data.get("close_fraction")
            
            if not partition_key or not row_key:
                logging.error("Missing required fields: partition_key and row_key")
                return False
            
            if atr_multiple is None or close_fraction is None:
                logging.error("Missing required fields: atr_multiple and close_fraction")
                return False
            
            # Validate data types and ranges
            atr_multiple_float = float(atr_multiple)
            close_fraction_int = int(close_fraction)
            
            if atr_multiple_float <= 0:
                logging.error("atr_multiple must be positive")
                return False
            
            if close_fraction_int <= 0 or close_fraction_int > 100:
                logging.error("close_fraction must be between 1 and 100")
                return False
            
            return True
        except (ValueError, TypeError) as e:
            logging.error(f"Data validation error: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            "partition_key": self.partition_key,
            "row_key": self.row_key,
            "atr_multiple": self.atr_multiple,
            "close_fraction": self.close_fraction
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp
        return result
