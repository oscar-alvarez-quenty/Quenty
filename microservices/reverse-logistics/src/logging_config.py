"""
Reverse Logistics Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "RL_E001": {
        "code": "RL_E001",
        "message": "Return request processing failed: {return_id} - {error_details}",
        "level": "ERROR",
        "description": "Product return request processing failed"
    },
    "RL_E002": {
        "code": "RL_E002",
        "message": "Return authorization failed: {return_id}",
        "level": "ERROR",
        "description": "Return authorization process encountered an error"
    },
    "RL_E003": {
        "code": "RL_E003",
        "message": "Refund processing failed: {refund_id} for return {return_id}",
        "level": "ERROR",
        "description": "Return refund processing failed"
    },
    "RL_E004": {
        "code": "RL_E004",
        "message": "Product inspection failed: {product_id} return {return_id}",
        "level": "ERROR",
        "description": "Returned product inspection process failed"
    },
    "RL_E005": {
        "code": "RL_E005",
        "message": "Inventory update failed: {product_id} after return processing",
        "level": "ERROR",
        "description": "Failed to update inventory after return processing"
    },
    "RL_E006": {
        "code": "RL_E006",
        "message": "Return shipping label generation failed: {return_id}",
        "level": "ERROR",
        "description": "Return shipping label creation failed"
    },
    "RL_E007": {
        "code": "RL_E007",
        "message": "Return status update failed: {return_id} to {status}",
        "level": "ERROR",
        "description": "Return status modification failed"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "RL_I001": {
        "code": "RL_I001",
        "message": "Return request created: {return_id} for order {order_id}",
        "level": "INFO",
        "description": "New return request created successfully"
    },
    "RL_I002": {
        "code": "RL_I002",
        "message": "Return authorized: {return_id} return label generated",
        "level": "INFO",
        "description": "Return request approved and shipping label created"
    },
    "RL_I003": {
        "code": "RL_I003",
        "message": "Product received: {return_id} items received at warehouse",
        "level": "INFO",
        "description": "Returned products received at processing facility"
    },
    "RL_I004": {
        "code": "RL_I004",
        "message": "Product inspection completed: {return_id} condition {condition}",
        "level": "INFO",
        "description": "Returned product inspection completed"
    },
    "RL_I005": {
        "code": "RL_I005",
        "message": "Refund processed: {refund_id} amount {refund_amount}",
        "level": "INFO",
        "description": "Return refund successfully processed"
    },
    "RL_I006": {
        "code": "RL_I006",
        "message": "Reverse logistics service started successfully on port {port}",
        "level": "INFO",
        "description": "Reverse logistics service initialization completed"
    },
    "RL_I007": {
        "code": "RL_I007",
        "message": "Product restocked: {product_id} quantity {quantity} after return",
        "level": "INFO",
        "description": "Returned product added back to inventory"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "RL_D001": {
        "code": "RL_D001",
        "message": "Processing return request: {request_type} for return {return_id}",
        "level": "DEBUG",
        "description": "Return request processing details"
    },
    "RL_D002": {
        "code": "RL_D002",
        "message": "Return eligibility check: {return_id} criteria {eligibility_criteria}",
        "level": "DEBUG",
        "description": "Return eligibility validation details"
    },
    "RL_D003": {
        "code": "RL_D003",
        "message": "Refund calculation: original {original_amount} refund {refund_amount}",
        "level": "DEBUG",
        "description": "Return refund amount calculation details"
    },
    "RL_D004": {
        "code": "RL_D004",
        "message": "Product condition assessment: {product_id} score {condition_score}",
        "level": "DEBUG",
        "description": "Returned product condition evaluation"
    },
    "RL_D005": {
        "code": "RL_D005",
        "message": "Return shipping tracking: {tracking_number} status {tracking_status}",
        "level": "DEBUG",
        "description": "Return shipment tracking details"
    },
    "RL_D006": {
        "code": "RL_D006",
        "message": "Database query: {query_type} for return {return_id} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Reverse logistics database operation performance"
    },
    "RL_D007": {
        "code": "RL_D007",
        "message": "Return reason analysis: {return_reason} category {reason_category}",
        "level": "DEBUG",
        "description": "Return reason categorization details"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "RL_W001": {
        "code": "RL_W001",
        "message": "High return rate detected: {product_id} return rate {return_percentage}%",
        "level": "WARNING",
        "description": "Product showing unusually high return rate"
    },
    "RL_W002": {
        "code": "RL_W002",
        "message": "Return processing delay: {return_id} processing time {processing_days} days",
        "level": "WARNING",
        "description": "Return taking longer than expected to process"
    },
    "RL_W003": {
        "code": "RL_W003",
        "message": "Product condition poor: {return_id} not suitable for resale",
        "level": "WARNING",
        "description": "Returned product in poor condition"
    },
    "RL_W004": {
        "code": "RL_W004",
        "message": "Refund amount high: {refund_amount} for return {return_id}",
        "level": "WARNING",
        "description": "Return refund amount unusually high"
    },
    "RL_W005": {
        "code": "RL_W005",
        "message": "Return fraud suspected: {return_id} risk indicators {risk_factors}",
        "level": "WARNING",
        "description": "Potential fraudulent return activity detected"
    },
    "RL_W006": {
        "code": "RL_W006",
        "message": "Warehouse capacity high: {warehouse_id} at {capacity_percentage}% capacity",
        "level": "WARNING",
        "description": "Return processing warehouse approaching capacity"
    },
    "RL_W007": {
        "code": "RL_W007",
        "message": "Reverse logistics service memory usage high: {memory_percentage}%",
        "level": "WARNING",
        "description": "Service memory usage approaching critical levels"
    }
}

# Combined logging messages for easy access
LOGGING_MESSAGES = {
    **ERROR_MESSAGES,
    **INFO_MESSAGES,
    **DEBUG_MESSAGES,
    **WARNING_MESSAGES
}