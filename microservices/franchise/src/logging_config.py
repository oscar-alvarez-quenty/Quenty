"""
Franchise Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "FRN_E001": {
        "code": "FRN_E001",
        "message": "Franchise registration failed: {franchise_id} - {error_details}",
        "level": "ERROR",
        "description": "Franchise registration process failed"
    },
    "FRN_E002": {
        "code": "FRN_E002",
        "message": "Franchise verification failed: {franchise_id}",
        "level": "ERROR",
        "description": "Franchise verification process encountered an error"
    },
    "FRN_E003": {
        "code": "FRN_E003",
        "message": "Territory assignment failed: {franchise_id} to {territory_id}",
        "level": "ERROR",
        "description": "Franchise territory assignment failed"
    },
    "FRN_E004": {
        "code": "FRN_E004",
        "message": "Commission calculation failed: {franchise_id} for period {period}",
        "level": "ERROR",
        "description": "Franchise commission calculation error"
    },
    "FRN_E005": {
        "code": "FRN_E005",
        "message": "Performance report generation failed: {franchise_id}",
        "level": "ERROR",
        "description": "Franchise performance report generation failed"
    },
    "FRN_E006": {
        "code": "FRN_E006",
        "message": "Training module assignment failed: {franchise_id} module {module_id}",
        "level": "ERROR",
        "description": "Franchise training assignment process failed"
    },
    "FRN_E007": {
        "code": "FRN_E007",
        "message": "Franchise status update failed: {franchise_id} to {status}",
        "level": "ERROR",
        "description": "Franchise status modification failed"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "FRN_I001": {
        "code": "FRN_I001",
        "message": "Franchise registered successfully: {franchise_id} owner {owner_name}",
        "level": "INFO",
        "description": "New franchise successfully registered"
    },
    "FRN_I002": {
        "code": "FRN_I002",
        "message": "Franchise verified: {franchise_id} verification completed",
        "level": "INFO",
        "description": "Franchise verification process completed successfully"
    },
    "FRN_I003": {
        "code": "FRN_I003",
        "message": "Territory assigned: {franchise_id} -> {territory_id}",
        "level": "INFO",
        "description": "Franchise territory assignment completed"
    },
    "FRN_I004": {
        "code": "FRN_I004",
        "message": "Commission paid: {franchise_id} amount {commission_amount}",
        "level": "INFO",
        "description": "Franchise commission payment processed"
    },
    "FRN_I005": {
        "code": "FRN_I005",
        "message": "Training completed: {franchise_id} module {module_name}",
        "level": "INFO",
        "description": "Franchise training module completed"
    },
    "FRN_I006": {
        "code": "FRN_I006",
        "message": "Franchise service started successfully on port {port}",
        "level": "INFO",
        "description": "Franchise service initialization completed"
    },
    "FRN_I007": {
        "code": "FRN_I007",
        "message": "Performance target achieved: {franchise_id} target {target_name}",
        "level": "INFO",
        "description": "Franchise achieved performance milestone"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "FRN_D001": {
        "code": "FRN_D001",
        "message": "Processing franchise request: {request_type} for franchise {franchise_id}",
        "level": "DEBUG",
        "description": "Franchise request processing details"
    },
    "FRN_D002": {
        "code": "FRN_D002",
        "message": "Territory availability check: {territory_id} status {availability_status}",
        "level": "DEBUG",
        "description": "Franchise territory availability validation"
    },
    "FRN_D003": {
        "code": "FRN_D003",
        "message": "Commission calculation: sales {sales_amount} rate {commission_rate}% = {commission}",
        "level": "DEBUG",
        "description": "Franchise commission calculation details"
    },
    "FRN_D004": {
        "code": "FRN_D004",
        "message": "Performance metrics: {franchise_id} KPIs {performance_metrics}",
        "level": "DEBUG",
        "description": "Franchise performance measurement details"
    },
    "FRN_D005": {
        "code": "FRN_D005",
        "message": "Training progress: {franchise_id} completed {completed_modules}/{total_modules}",
        "level": "DEBUG",
        "description": "Franchise training progress tracking"
    },
    "FRN_D006": {
        "code": "FRN_D006",
        "message": "Database query: {query_type} for franchise {franchise_id} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Franchise database operation performance"
    },
    "FRN_D007": {
        "code": "FRN_D007",
        "message": "Document verification: {document_type} status {verification_status}",
        "level": "DEBUG",
        "description": "Franchise document verification details"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "FRN_W001": {
        "code": "FRN_W001",
        "message": "Franchise performance below target: {franchise_id} ({performance_percentage}% of target)",
        "level": "WARNING",
        "description": "Franchise not meeting performance expectations"
    },
    "FRN_W002": {
        "code": "FRN_W002",
        "message": "Training overdue: {franchise_id} module {module_name} overdue by {days_overdue} days",
        "level": "WARNING",
        "description": "Franchise training module completion overdue"
    },
    "FRN_W003": {
        "code": "FRN_W003",
        "message": "Territory overlap detected: {territory_id} with {conflicting_franchise}",
        "level": "WARNING",
        "description": "Potential franchise territory boundary conflict"
    },
    "FRN_W004": {
        "code": "FRN_W004",
        "message": "Commission payment delay: {franchise_id} payment {days_delayed} days overdue",
        "level": "WARNING",
        "description": "Franchise commission payment is overdue"
    },
    "FRN_W005": {
        "code": "FRN_W005",
        "message": "Low franchise activity: {franchise_id} no orders in {inactive_days} days",
        "level": "WARNING",
        "description": "Franchise showing low business activity"
    },
    "FRN_W006": {
        "code": "FRN_W006",
        "message": "High support ticket volume: {franchise_id} ({ticket_count} tickets this month)",
        "level": "WARNING",
        "description": "Franchise generating high number of support requests"
    },
    "FRN_W007": {
        "code": "FRN_W007",
        "message": "Franchise service memory usage high: {memory_percentage}%",
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