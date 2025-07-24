"""
Pickup Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "PKP_E001": {
        "code": "PKP_E001",
        "message": "Pickup scheduling failed: {error_details}",
        "level": "ERROR",
        "description": "Pickup appointment scheduling process failed"
    },
    "PKP_E002": {
        "code": "PKP_E002",
        "message": "Pickup not found: {pickup_id}",
        "level": "ERROR",
        "description": "Requested pickup ID does not exist"
    },
    "PKP_E003": {
        "code": "PKP_E003",
        "message": "Pickup assignment failed: {pickup_id} to driver {driver_id}",
        "level": "ERROR",
        "description": "Failed to assign pickup to available driver"
    },
    "PKP_E004": {
        "code": "PKP_E004",
        "message": "GPS tracking failed for pickup: {pickup_id}",
        "level": "ERROR",
        "description": "GPS location tracking system error"
    },
    "PKP_E005": {
        "code": "PKP_E005",
        "message": "Pickup status update failed: {pickup_id}",
        "level": "ERROR",
        "description": "Pickup status modification failed"
    },
    "PKP_E006": {
        "code": "PKP_E006",
        "message": "Route optimization failed: {route_details}",
        "level": "ERROR",
        "description": "Pickup route calculation error"
    },
    "PKP_E007": {
        "code": "PKP_E007",
        "message": "Pickup cancellation failed: {pickup_id}",
        "level": "ERROR",
        "description": "Pickup cancellation process failed"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "PKP_I001": {
        "code": "PKP_I001",
        "message": "Pickup scheduled successfully: {pickup_id} for {pickup_date}",
        "level": "INFO",
        "description": "Pickup appointment created successfully"
    },
    "PKP_I002": {
        "code": "PKP_I002",
        "message": "Pickup assigned to driver: {pickup_id} -> {driver_id}",
        "level": "INFO",
        "description": "Pickup successfully assigned to available driver"
    },
    "PKP_I003": {
        "code": "PKP_I003",
        "message": "Pickup completed: {pickup_id}",
        "level": "INFO",
        "description": "Pickup successfully completed by driver"
    },
    "PKP_I004": {
        "code": "PKP_I004",
        "message": "Route optimized: {route_id} with {stops_count} stops",
        "level": "INFO",
        "description": "Pickup route optimization completed"
    },
    "PKP_I005": {
        "code": "PKP_I005",
        "message": "Driver location updated: {driver_id} at {location}",
        "level": "INFO",
        "description": "Driver GPS location tracking updated"
    },
    "PKP_I006": {
        "code": "PKP_I006",
        "message": "Pickup service started successfully on port {port}",
        "level": "INFO",
        "description": "Pickup service initialization completed"
    },
    "PKP_I007": {
        "code": "PKP_I007",
        "message": "Pickup notification sent: {pickup_id} to customer {customer_id}",
        "level": "INFO",
        "description": "Customer notification about pickup status sent"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "PKP_D001": {
        "code": "PKP_D001",
        "message": "Processing pickup request: {request_type} for {pickup_id}",
        "level": "DEBUG",
        "description": "Pickup request processing details"
    },
    "PKP_D002": {
        "code": "PKP_D002",
        "message": "Driver availability check: {driver_count} available drivers",
        "level": "DEBUG",
        "description": "Available driver pool status"
    },
    "PKP_D003": {
        "code": "PKP_D003",
        "message": "GPS coordinates: {latitude}, {longitude} for pickup {pickup_id}",
        "level": "DEBUG",
        "description": "Pickup location coordinates"
    },
    "PKP_D004": {
        "code": "PKP_D004",
        "message": "Route calculation: {calculation_details}",
        "level": "DEBUG",
        "description": "Pickup route calculation process details"
    },
    "PKP_D005": {
        "code": "PKP_D005",
        "message": "Time slot availability: {time_slot} status {availability}",
        "level": "DEBUG",
        "description": "Pickup time slot availability check"
    },
    "PKP_D006": {
        "code": "PKP_D006",
        "message": "Pickup database query: {query_type} in {execution_time}ms",
        "level": "DEBUG",
        "description": "Pickup database operation performance"
    },
    "PKP_D007": {
        "code": "PKP_D007",
        "message": "Distance calculation: {distance}km between {origin} and {destination}",
        "level": "DEBUG",
        "description": "Pickup distance calculation result"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "PKP_W001": {
        "code": "PKP_W001",
        "message": "Limited driver availability: {available_drivers} drivers for {pending_pickups} pickups",
        "level": "WARNING",
        "description": "Driver capacity approaching limits"
    },
    "PKP_W002": {
        "code": "PKP_W002",
        "message": "Pickup delay detected: {pickup_id} delayed by {delay_minutes} minutes",
        "level": "WARNING",
        "description": "Pickup running behind scheduled time"
    },
    "PKP_W003": {
        "code": "PKP_W003",
        "message": "High route optimization time: {optimization_time}ms",
        "level": "WARNING",
        "description": "Route calculation performance degradation"
    },
    "PKP_W004": {
        "code": "PKP_W004",
        "message": "GPS signal weak for driver: {driver_id}",
        "level": "WARNING",
        "description": "Poor GPS signal quality affecting tracking"
    },
    "PKP_W005": {
        "code": "PKP_W005",
        "message": "Pickup rescheduled multiple times: {pickup_id} ({reschedule_count} times)",
        "level": "WARNING",
        "description": "Pickup has been rescheduled excessively"
    },
    "PKP_W006": {
        "code": "PKP_W006",
        "message": "High pickup density in area: {area_code} ({pickups_count} pickups)",
        "level": "WARNING",
        "description": "Concentrated pickup activity in specific area"
    },
    "PKP_W007": {
        "code": "PKP_W007",
        "message": "Pickup service memory usage high: {memory_percentage}%",
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