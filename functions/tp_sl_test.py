"""
Test script for Take Profit and Stop Loss REST endpoints.
This script demonstrates how to use the TP/SL CRUD operations.
"""

import json
import logging
from models.tp_sl_info import TakeProfitStopLossInfo
from managers.tp_sl_manager import TpSlManager

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_tp_sl_operations():
    """Test all CRUD operations for TP/SL records."""
    print("=== Testing TP/SL CRUD Operations ===\n")
    
    # Initialize manager
    manager = TpSlManager()
    
    # Test data
    test_data = {
        "partition_key": "tp",
        "row_key": "test_1",
        "atr_multiple": 0.5,
        "close_fraction": 30
    }
    
    try:
        # Test 1: Create record
        print("1. Creating TP/SL record...")
        tp_sl_info = TakeProfitStopLossInfo.from_dict(test_data)
        success = manager.create_tp_sl(tp_sl_info)
        print(f"   Create result: {'Success' if success else 'Failed'}")
        
        # Test 2: Read record
        print("\n2. Reading TP/SL record...")
        retrieved_record = manager.get_tp_sl(test_data["partition_key"], test_data["row_key"])
        if retrieved_record:
            print(f"   Retrieved: {retrieved_record.to_dict()}")
        else:
            print("   No record found")
        
        # Test 3: Update record
        print("\n3. Updating TP/SL record...")
        test_data["atr_multiple"] = 0.8
        test_data["close_fraction"] = 40
        updated_tp_sl_info = TakeProfitStopLossInfo.from_dict(test_data)
        success = manager.update_tp_sl(updated_tp_sl_info)
        print(f"   Update result: {'Success' if success else 'Failed'}")
        
        # Test 4: List all records
        print("\n4. Listing all TP/SL records...")
        all_records = manager.list_all_tp_sl()
        print(f"   Found {len(all_records)} records")
        for record in all_records:
            print(f"   - {record.to_dict()}")
        
        # Test 5: Delete record
        print("\n5. Deleting TP/SL record...")
        success = manager.delete_tp_sl(test_data["partition_key"], test_data["row_key"])
        print(f"   Delete result: {'Success' if success else 'Failed'}")
        
        print("\n=== Test completed ===")
        
    except Exception as e:
        print(f"Error during testing: {e}")

def test_data_validation():
    """Test data validation for TP/SL records."""
    print("\n=== Testing Data Validation ===\n")
    
    # Valid data
    valid_data = {
        "partition_key": "tp",
        "row_key": "1",
        "atr_multiple": 0.5,
        "close_fraction": 30
    }
    
    # Invalid data examples
    invalid_data_examples = [
        {"atr_multiple": 0.5, "close_fraction": 30},  # Missing keys
        {"partition_key": "tp", "row_key": "1", "atr_multiple": -0.5, "close_fraction": 30},  # Negative atr_multiple
        {"partition_key": "tp", "row_key": "1", "atr_multiple": 0.5, "close_fraction": 150},  # Invalid close_fraction
        {"partition_key": "tp", "row_key": "1", "atr_multiple": "invalid", "close_fraction": 30},  # Invalid type
    ]
    
    print("Testing valid data:")
    try:
        tp_sl_info = TakeProfitStopLossInfo.from_dict(valid_data)
        print(f"   ✓ Valid data accepted: {tp_sl_info.to_dict()}")
    except Exception as e:
        print(f"   ✗ Valid data rejected: {e}")
    
    print("\nTesting invalid data:")
    for i, invalid_data in enumerate(invalid_data_examples, 1):
        try:
            tp_sl_info = TakeProfitStopLossInfo.from_dict(invalid_data)
            print(f"   ✗ Invalid data {i} accepted (should have been rejected): {invalid_data}")
        except Exception as e:
            print(f"   ✓ Invalid data {i} correctly rejected: {invalid_data}")

if __name__ == "__main__":
    # Run validation tests first (these don't require Azure connection)
    test_data_validation()
    
    # Uncomment the line below to test actual CRUD operations
    # (requires Azure Storage connection to be configured)
    # test_tp_sl_operations()
