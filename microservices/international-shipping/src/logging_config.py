"""
International Shipping Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "INTL_E001": {
        "code": "INTL_E001",
        "message": "International shipment creation failed: {error_details}",
        "level": "ERROR",
        "description": "International shipment creation process failed"
    },
    "INTL_E002": {
        "code": "INTL_E002",
        "message": "Customs documentation generation failed: {shipment_id}",
        "level": "ERROR",
        "description": "Customs forms generation encountered an error"
    },
    "INTL_E003": {
        "code": "INTL_E003",
        "message": "Shipping rate calculation failed: {route_details}",
        "level": "ERROR",
        "description": "International shipping cost calculation error"
    },
    "INTL_E004": {
        "code": "INTL_E004",
        "message": "Tracking update failed: {tracking_number}",
        "level": "ERROR",
        "description": "International shipment tracking update failed"
    },
    "INTL_E005": {
        "code": "INTL_E005",
        "message": "Carrier API error: {carrier_name} - {error_message}",
        "level": "ERROR",
        "description": "External shipping carrier API error"
    },
    "INTL_E006": {
        "code": "INTL_E006",
        "message": "Address validation failed: {destination_country}",
        "level": "ERROR",
        "description": "International destination address validation failed"
    },
    "INTL_E007": {
        "code": "INTL_E007",
        "message": "Currency conversion failed: {from_currency} to {to_currency}",
        "level": "ERROR",
        "description": "Currency conversion service error"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "INTL_I001": {
        "code": "INTL_I001",
        "message": "International shipment created: {shipment_id} to {destination_country}",
        "level": "INFO",
        "description": "International shipment successfully created"
    },
    "INTL_I002": {
        "code": "INTL_I002",
        "message": "Customs documentation generated: {shipment_id}",
        "level": "INFO",
        "description": "Customs forms successfully generated"
    },
    "INTL_I003": {
        "code": "INTL_I003",
        "message": "Shipment dispatched: {shipment_id} via {carrier_name}",
        "level": "INFO",
        "description": "International shipment handed over to carrier"
    },
    "INTL_I004": {
        "code": "INTL_I004",
        "message": "Shipment cleared customs: {shipment_id} in {country}",
        "level": "INFO",
        "description": "Shipment successfully cleared customs"
    },
    "INTL_I005": {
        "code": "INTL_I005",
        "message": "International delivery completed: {shipment_id}",
        "level": "INFO",
        "description": "International shipment delivered successfully"
    },
    "INTL_I006": {
        "code": "INTL_I006",
        "message": "International shipping service started on port {port}",
        "level": "INFO",
        "description": "International shipping service initialization completed"
    },
    "INTL_I007": {
        "code": "INTL_I007",
        "message": "Exchange rate updated: {currency_pair} = {exchange_rate}",
        "level": "INFO",
        "description": "Currency exchange rate successfully updated"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "INTL_D001": {
        "code": "INTL_D001",
        "message": "Processing international shipping request: {request_type}",
        "level": "DEBUG",
        "description": "International shipping request processing details"
    },
    "INTL_D002": {
        "code": "INTL_D002",
        "message": "Carrier API request: {carrier_name} endpoint {endpoint}",
        "level": "DEBUG",
        "description": "External carrier API call details"
    },
    "INTL_D003": {
        "code": "INTL_D003",
        "message": "Duty calculation: {item_category} value {item_value} duty {duty_amount}",
        "level": "DEBUG",
        "description": "Customs duty calculation details"
    },
    "INTL_D004": {
        "code": "INTL_D004",
        "message": "Shipping zone lookup: {country_code} -> zone {shipping_zone}",
        "level": "DEBUG",
        "description": "International shipping zone determination"
    },
    "INTL_D005": {
        "code": "INTL_D005",
        "message": "Document validation: {document_type} status {validation_status}",
        "level": "DEBUG",
        "description": "Shipping document validation details"
    },
    "INTL_D006": {
        "code": "INTL_D006",
        "message": "Transit time calculation: {origin} to {destination} = {transit_days} days",
        "level": "DEBUG",
        "description": "International transit time calculation"
    },
    "INTL_D007": {
        "code": "INTL_D007",
        "message": "Package dimensions: {length}x{width}x{height}cm weight {weight}kg",
        "level": "DEBUG",
        "description": "Package physical specifications"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "INTL_W001": {
        "code": "INTL_W001",
        "message": "High shipping cost: {shipment_id} cost {shipping_cost} ({cost_percentage}% of value)",
        "level": "WARNING",
        "description": "Shipping cost unusually high relative to package value"
    },
    "INTL_W002": {
        "code": "INTL_W002",
        "message": "Customs delay detected: {shipment_id} held for {delay_days} days",
        "level": "WARNING",
        "description": "Shipment delayed in customs processing"
    },
    "INTL_W003": {
        "code": "INTL_W003",
        "message": "Carrier service disruption: {carrier_name} in {affected_region}",
        "level": "WARNING",
        "description": "Shipping carrier experiencing service issues"
    },
    "INTL_W004": {
        "code": "INTL_W004",
        "message": "Exchange rate volatility: {currency_pair} changed {change_percentage}%",
        "level": "WARNING",
        "description": "Significant currency exchange rate fluctuation"
    },
    "INTL_W005": {
        "code": "INTL_W005",
        "message": "Restricted item detected: {item_description} to {destination_country}",
        "level": "WARNING",
        "description": "Package contains items restricted for destination"
    },
    "INTL_W006": {
        "code": "INTL_W006",
        "message": "High tracking update latency: {tracking_number} last update {hours_ago}h ago",
        "level": "WARNING",
        "description": "Tracking information not updated recently"
    },
    "INTL_W007": {
        "code": "INTL_W007",
        "message": "International shipping service memory usage high: {memory_percentage}%",
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