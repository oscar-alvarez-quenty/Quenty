"""
Customer Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "CUST_E001": {
        "code": "CUST_E001",
        "message": "Failed to create customer: {error_details}",
        "level": "ERROR",
        "description": "Customer creation process failed"
    },
    "CUST_E002": {
        "code": "CUST_E002",
        "message": "Customer not found: {customer_id}",
        "level": "ERROR",
        "description": "Requested customer ID does not exist"
    },
    "CUST_E003": {
        "code": "CUST_E003",
        "message": "Customer update failed: {customer_id} - {error_details}",
        "level": "ERROR",
        "description": "Customer information update operation failed"
    },
    "CUST_E004": {
        "code": "CUST_E004",
        "message": "Customer deletion failed: {customer_id}",
        "level": "ERROR",
        "description": "Customer account deletion process failed"
    },
    "CUST_E005": {
        "code": "CUST_E005",
        "message": "Customer address validation failed: {address_details}",
        "level": "ERROR",
        "description": "Customer address information validation failed"
    },
    "CUST_E006": {
        "code": "CUST_E006",
        "message": "Customer preferences update failed: {customer_id}",
        "level": "ERROR",
        "description": "Customer preferences modification failed"
    },
    "CUST_E007": {
        "code": "CUST_E007",
        "message": "Customer search query failed: {search_criteria}",
        "level": "ERROR",
        "description": "Customer search operation encountered an error"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "CUST_I001": {
        "code": "CUST_I001",
        "message": "Customer created successfully: {customer_id}",
        "level": "INFO",
        "description": "New customer account created successfully"
    },
    "CUST_I002": {
        "code": "CUST_I002",
        "message": "Customer profile updated: {customer_id}",
        "level": "INFO",
        "description": "Customer profile information updated successfully"
    },
    "CUST_I003": {
        "code": "CUST_I003",
        "message": "Customer address added: {customer_id}",
        "level": "INFO",
        "description": "New address added to customer profile"
    },
    "CUST_I004": {
        "code": "CUST_I004",
        "message": "Customer preferences updated: {customer_id}",
        "level": "INFO",
        "description": "Customer preferences modified successfully"
    },
    "CUST_I005": {
        "code": "CUST_I005",
        "message": "Customer search completed: {results_count} results",
        "level": "INFO",
        "description": "Customer search operation completed successfully"
    },
    "CUST_I006": {
        "code": "CUST_I006",
        "message": "Customer service started successfully on port {port}",
        "level": "INFO",
        "description": "Customer service initialization completed"
    },
    "CUST_I007": {
        "code": "CUST_I007",
        "message": "Customer loyalty status updated: {customer_id} to {status}",
        "level": "INFO",
        "description": "Customer loyalty tier modified"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "CUST_D001": {
        "code": "CUST_D001",
        "message": "Processing customer request: {request_type} for {customer_id}",
        "level": "DEBUG",
        "description": "Customer request processing details"
    },
    "CUST_D002": {
        "code": "CUST_D002",
        "message": "Customer data validation: {validation_details}",
        "level": "DEBUG",
        "description": "Customer data validation process details"
    },
    "CUST_D003": {
        "code": "CUST_D003",
        "message": "Database query for customer: {query_type} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Customer database operation performance"
    },
    "CUST_D004": {
        "code": "CUST_D004",
        "message": "Customer cache operation: {operation} for key {cache_key}",
        "level": "DEBUG",
        "description": "Customer data caching operation details"
    },
    "CUST_D005": {
        "code": "CUST_D005",
        "message": "Address geocoding result: {geocoding_result}",
        "level": "DEBUG",
        "description": "Customer address geocoding process result"
    },
    "CUST_D006": {
        "code": "CUST_D006",
        "message": "Customer notification sent: {notification_type} to {customer_id}",
        "level": "DEBUG",
        "description": "Customer notification delivery details"
    },
    "CUST_D007": {
        "code": "CUST_D007",
        "message": "Customer analytics event: {event_type} for {customer_id}",
        "level": "DEBUG",
        "description": "Customer behavior analytics event tracking"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "CUST_W001": {
        "code": "CUST_W001",
        "message": "Duplicate customer email detected: {email}",
        "level": "WARNING",
        "description": "Attempt to create customer with existing email"
    },
    "CUST_W002": {
        "code": "CUST_W002",
        "message": "Customer data incomplete: {customer_id} missing {missing_fields}",
        "level": "WARNING",
        "description": "Customer profile has missing required information"
    },
    "CUST_W003": {
        "code": "CUST_W003",
        "message": "High customer query response time: {response_time}ms",
        "level": "WARNING",
        "description": "Customer database query performance degradation"
    },
    "CUST_W004": {
        "code": "CUST_W004",
        "message": "Customer account locked: {customer_id}",
        "level": "WARNING",
        "description": "Customer account has been locked due to suspicious activity"
    },
    "CUST_W005": {
        "code": "CUST_W005",
        "message": "Invalid address format for customer: {customer_id}",
        "level": "WARNING",
        "description": "Customer address does not meet validation criteria"
    },
    "CUST_W006": {
        "code": "CUST_W006",
        "message": "Customer service memory usage high: {memory_percentage}%",
        "level": "WARNING",
        "description": "Service memory usage approaching critical levels"
    },
    "CUST_W007": {
        "code": "CUST_W007",
        "message": "Customer notification delivery failed: {customer_id}",
        "level": "WARNING",
        "description": "Failed to deliver notification to customer"
    }
}

# Combined logging messages for easy access
LOGGING_MESSAGES = {
    **ERROR_MESSAGES,
    **INFO_MESSAGES,
    **DEBUG_MESSAGES,
    **WARNING_MESSAGES
}