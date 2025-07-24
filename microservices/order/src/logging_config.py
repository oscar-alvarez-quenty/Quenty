"""
Order Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "ORD_E001": {
        "code": "ORD_E001",
        "message": "Order creation failed: {error_details}",
        "level": "ERROR",
        "description": "Order creation process encountered an error"
    },
    "ORD_E002": {
        "code": "ORD_E002",
        "message": "Order not found: {order_id}",
        "level": "ERROR",
        "description": "Requested order ID does not exist"
    },
    "ORD_E003": {
        "code": "ORD_E003",
        "message": "Order status update failed: {order_id} to {status}",
        "level": "ERROR",
        "description": "Order status modification failed"
    },
    "ORD_E004": {
        "code": "ORD_E004",
        "message": "Payment processing failed for order: {order_id}",
        "level": "ERROR",
        "description": "Payment gateway processing error"
    },
    "ORD_E005": {
        "code": "ORD_E005",
        "message": "Inventory check failed for order: {order_id}",
        "level": "ERROR",
        "description": "Product inventory validation failed"
    },
    "ORD_E006": {
        "code": "ORD_E006",
        "message": "Order cancellation failed: {order_id}",
        "level": "ERROR",
        "description": "Order cancellation process failed"
    },
    "ORD_E007": {
        "code": "ORD_E007",
        "message": "Shipping calculation failed for order: {order_id}",
        "level": "ERROR",
        "description": "Shipping cost calculation error"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "ORD_I001": {
        "code": "ORD_I001",
        "message": "Order created successfully: {order_id} for customer {customer_id}",
        "level": "INFO",
        "description": "New order created successfully"
    },
    "ORD_I002": {
        "code": "ORD_I002",
        "message": "Order status updated: {order_id} to {status}",
        "level": "INFO",
        "description": "Order status changed successfully"
    },
    "ORD_I003": {
        "code": "ORD_I003",
        "message": "Payment confirmed for order: {order_id}",
        "level": "INFO",
        "description": "Order payment processed successfully"
    },
    "ORD_I004": {
        "code": "ORD_I004",
        "message": "Order shipped: {order_id} with tracking {tracking_number}",
        "level": "INFO",
        "description": "Order dispatched for delivery"
    },
    "ORD_I005": {
        "code": "ORD_I005",
        "message": "Order delivered: {order_id}",
        "level": "INFO",
        "description": "Order successfully delivered to customer"
    },
    "ORD_I006": {
        "code": "ORD_I006",
        "message": "Order service started successfully on port {port}",
        "level": "INFO",
        "description": "Order service initialization completed"
    },
    "ORD_I007": {
        "code": "ORD_I007",
        "message": "Order refund processed: {order_id} amount {refund_amount}",
        "level": "INFO",
        "description": "Order refund completed successfully"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "ORD_D001": {
        "code": "ORD_D001",
        "message": "Processing order request: {request_type} for order {order_id}",
        "level": "DEBUG",
        "description": "Order request processing details"
    },
    "ORD_D002": {
        "code": "ORD_D002",
        "message": "Order validation: {validation_details}",
        "level": "DEBUG",
        "description": "Order data validation process details"
    },
    "ORD_D003": {
        "code": "ORD_D003",
        "message": "Inventory check result: {product_id} available {quantity}",
        "level": "DEBUG",
        "description": "Product availability check result"
    },
    "ORD_D004": {
        "code": "ORD_D004",
        "message": "Payment gateway request: {gateway} for amount {amount}",
        "level": "DEBUG",
        "description": "Payment processing request details"
    },
    "ORD_D005": {
        "code": "ORD_D005",
        "message": "Shipping calculation: {shipping_details}",
        "level": "DEBUG",
        "description": "Shipping cost calculation details"
    },
    "ORD_D006": {
        "code": "ORD_D006",
        "message": "Order database query: {query_type} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Order database operation performance"
    },
    "ORD_D007": {
        "code": "ORD_D007",
        "message": "Order workflow step: {workflow_step} for order {order_id}",
        "level": "DEBUG",
        "description": "Order processing workflow step details"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "ORD_W001": {
        "code": "ORD_W001",
        "message": "Low inventory for product: {product_id} (remaining: {quantity})",
        "level": "WARNING",
        "description": "Product inventory below minimum threshold"
    },
    "ORD_W002": {
        "code": "ORD_W002",
        "message": "High order processing time: {processing_time}ms for order {order_id}",
        "level": "WARNING",
        "description": "Order processing performance degradation"
    },
    "ORD_W003": {
        "code": "ORD_W003",
        "message": "Payment gateway timeout for order: {order_id}",
        "level": "WARNING",
        "description": "Payment processing taking longer than expected"
    },
    "ORD_W004": {
        "code": "ORD_W004",
        "message": "Order modification after confirmation: {order_id}",
        "level": "WARNING",
        "description": "Attempt to modify confirmed order"
    },
    "ORD_W005": {
        "code": "ORD_W005",
        "message": "Unusual order pattern detected: {pattern_details}",
        "level": "WARNING",
        "description": "Potentially fraudulent order behavior detected"
    },
    "ORD_W006": {
        "code": "ORD_W006",
        "message": "Order service memory usage high: {memory_percentage}%",
        "level": "WARNING",
        "description": "Service memory usage approaching critical levels"
    },
    "ORD_W007": {
        "code": "ORD_W007",
        "message": "Shipping delay for order: {order_id} estimated delay {delay_hours}h",
        "level": "WARNING",
        "description": "Order shipment delayed beyond normal timeframe"
    }
}

# Combined logging messages for easy access
LOGGING_MESSAGES = {
    **ERROR_MESSAGES,
    **INFO_MESSAGES,
    **DEBUG_MESSAGES,
    **WARNING_MESSAGES
}