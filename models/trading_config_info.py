from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from datetime import datetime

@dataclass
class TradingConfigInfoData:
    """Data class for Trading Configuration information"""
    leverage: int
    wallet_allocation: float
    row_key: Optional[str] = None
    partition_key: Optional[str] = None
    timestamp: Optional[Union[datetime, str]] = None
    
    def to_entity(self) -> Dict[str, Any]:
        """Convert to Azure Table Storage entity format"""
        entity = {
            "PartitionKey": self.partition_key,
            "RowKey": self.row_key,
            "LEVERAGE": self.leverage,
            "WALLET_ALLOCATION": self.wallet_allocation
        }
        if self.timestamp:
            entity["Timestamp"] = self.timestamp
        return entity
    
    @classmethod
    def from_entity(cls, entity: Dict[str, Any]) -> 'TradingConfigInfoData':
        """Create instance from Azure Table Storage entity"""
        import logging
        
        # Debug: Log all available keys in the entity
        logging.info(f"Entity keys: {list(entity.keys())}")
        logging.info(f"Full entity: {entity}")
        
        # Try different timestamp field names that Azure Table Storage might use
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
            leverage=int(entity.get("LEVERAGE", 1)),
            wallet_allocation=float(entity.get("WALLET_ALLOCATION", 0.0)),
            row_key=entity.get("RowKey"),
            partition_key=entity.get("PartitionKey"),
            timestamp=timestamp
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingConfigInfoData':
        """Create instance from dictionary (e.g., from HTTP request)"""
        # Support both "id" and "RowKey" formats
        row_key = data.get("id") or data.get("RowKey")
        # Support custom PartitionKey, use row_key as default (symbol)
        partition_key = data.get("PartitionKey", row_key)
        
        return cls(
            leverage=int(data.get("leverage") or data.get("LEVERAGE", 1)),
            wallet_allocation=float(data.get("wallet_allocation") or data.get("WALLET_ALLOCATION", 0.0)),
            row_key=row_key,
            partition_key=partition_key
        )
    
    def validate(self) -> bool:
        """Validate the data"""
        return (
            self.leverage > 0 and
            self.wallet_allocation > 0 and
            self.wallet_allocation <= 1.0 and  # Assuming max 100% allocation
            self.row_key is not None and
            self.partition_key is not None
        )

# models/trading_config_info.py

from typing import TypedDict

class TradingConfigInfoDict(TypedDict):
    """
    A dictionary representing the trading configuration for a symbol.
    """
    PartitionKey: str
    RowKey: str
    leverage: int
    wallet_allocation: float
    chart_time_interval: str
    atr_candles: int
