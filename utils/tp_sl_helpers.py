from typing import Dict, Any, Optional
import json
import logging

def parse_request_body(request_body: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON request body safely.
    
    Args:
        request_body: Raw request body string
        
    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        if not request_body:
            return None
        return json.loads(request_body)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON request body: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error parsing request body: {e}")
        return None

def validate_required_params(params: Dict[str, Any], required_fields: list) -> tuple[bool, str]:
    """
    Validate that all required parameters are present and not empty.
    
    Args:
        params: Dictionary of parameters to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in params or params[field] is None or str(params[field]).strip() == "":
            missing_fields.append(field)
    
    if missing_fields:
        error_msg = f"Missing or empty required fields: {', '.join(missing_fields)}"
        return False, error_msg
    
    return True, ""

def sanitize_string(value: Any) -> str:
    """
    Safely convert any value to a string and strip whitespace.
    
    Args:
        value: Value to convert to string
        
    Returns:
        Sanitized string
    """
    if value is None:
        return ""
    return str(value).strip()

def format_response_message(operation: str, partition_key: str, row_key: str, success: bool) -> str:
    """
    Format a standard response message for CRUD operations.
    
    Args:
        operation: The operation performed (e.g., 'created', 'updated', 'deleted')
        partition_key: The partition key of the record
        row_key: The row key of the record
        success: Whether the operation was successful
        
    Returns:
        Formatted message string
    """
    status = "successfully" if success else "failed to be"
    return f"TP/SL record (PK={partition_key}, RK={row_key}) {status} {operation}"
