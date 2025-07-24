"""
Analytics Service Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "ANL_E001": {
        "code": "ANL_E001",
        "message": "Data aggregation failed: {aggregation_type} - {error_details}",
        "level": "ERROR",
        "description": "Analytics data aggregation process failed"
    },
    "ANL_E002": {
        "code": "ANL_E002",
        "message": "Report generation failed: {report_type}",
        "level": "ERROR",
        "description": "Analytics report generation encountered an error"
    },
    "ANL_E003": {
        "code": "ANL_E003",
        "message": "Data pipeline failure: {pipeline_name} - {error_message}",
        "level": "ERROR",
        "description": "Analytics data pipeline processing failed"
    },
    "ANL_E004": {
        "code": "ANL_E004",
        "message": "Metric calculation failed: {metric_name}",
        "level": "ERROR",
        "description": "Business metric calculation error"
    },
    "ANL_E005": {
        "code": "ANL_E005",
        "message": "Dashboard update failed: {dashboard_id}",
        "level": "ERROR",
        "description": "Analytics dashboard refresh failed"
    },
    "ANL_E006": {
        "code": "ANL_E006",
        "message": "Data export failed: {export_format} - {error_details}",
        "level": "ERROR",
        "description": "Analytics data export process failed"
    },
    "ANL_E007": {
        "code": "ANL_E007",
        "message": "Real-time processing failed: {stream_name}",
        "level": "ERROR",
        "description": "Real-time analytics stream processing error"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "ANL_I001": {
        "code": "ANL_I001",
        "message": "Report generated successfully: {report_type} for period {time_period}",
        "level": "INFO",
        "description": "Analytics report generated successfully"
    },
    "ANL_I002": {
        "code": "ANL_I002",
        "message": "Data aggregation completed: {record_count} records processed",
        "level": "INFO",
        "description": "Data aggregation process completed successfully"
    },
    "ANL_I003": {
        "code": "ANL_I003",
        "message": "Dashboard updated: {dashboard_id} with {widget_count} widgets",
        "level": "INFO",
        "description": "Analytics dashboard successfully refreshed"
    },
    "ANL_I004": {
        "code": "ANL_I004",
        "message": "KPI calculation completed: {kpi_name} value {kpi_value}",
        "level": "INFO",
        "description": "Key performance indicator successfully calculated"
    },
    "ANL_I005": {
        "code": "ANL_I005",
        "message": "Data export completed: {export_format} {record_count} records",
        "level": "INFO",
        "description": "Analytics data export completed successfully"
    },
    "ANL_I006": {
        "code": "ANL_I006",
        "message": "Analytics service started successfully on port {port}",
        "level": "INFO",
        "description": "Analytics service initialization completed"
    },
    "ANL_I007": {
        "code": "ANL_I007",
        "message": "Alert triggered: {alert_name} threshold {threshold_value}",
        "level": "INFO",
        "description": "Analytics alert condition met"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "ANL_D001": {
        "code": "ANL_D001",
        "message": "Processing analytics request: {request_type} for timeframe {timeframe}",
        "level": "DEBUG",
        "description": "Analytics request processing details"
    },
    "ANL_D002": {
        "code": "ANL_D002",
        "message": "Query execution: {query_type} returned {result_count} rows in {execution_time}ms",
        "level": "DEBUG",
        "description": "Analytics database query performance"
    },
    "ANL_D003": {
        "code": "ANL_D003",
        "message": "Data transformation: {transformation_type} applied to {dataset_name}",
        "level": "DEBUG",
        "description": "Data transformation process details"
    },
    "ANL_D004": {
        "code": "ANL_D004",
        "message": "Metric calculation: {metric_name} = {calculation_formula}",
        "level": "DEBUG",
        "description": "Business metric calculation formula"
    },
    "ANL_D005": {
        "code": "ANL_D005",
        "message": "Cache operation: {operation_type} for key {cache_key}",
        "level": "DEBUG",
        "description": "Analytics cache operation details"
    },
    "ANL_D006": {
        "code": "ANL_D006",
        "message": "Data source connection: {source_type} status {connection_status}",
        "level": "DEBUG",
        "description": "External data source connection status"
    },
    "ANL_D007": {
        "code": "ANL_D007",
        "message": "Trend analysis: {trend_type} showing {trend_direction} over {time_period}",
        "level": "DEBUG",
        "description": "Trend analysis calculation details"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "ANL_W001": {
        "code": "ANL_W001",
        "message": "High query execution time: {execution_time}ms for query {query_type}",
        "level": "WARNING",
        "description": "Analytics query performance degradation"
    },
    "ANL_W002": {
        "code": "ANL_W002",
        "message": "Data quality issue: {quality_issue} in dataset {dataset_name}",
        "level": "WARNING",
        "description": "Data quality anomaly detected"
    },
    "ANL_W003": {
        "code": "ANL_W003",
        "message": "Missing data detected: {missing_data_type} for period {time_period}",
        "level": "WARNING",
        "description": "Expected data not available for analysis"
    },
    "ANL_W004": {
        "code": "ANL_W004",
        "message": "Metric threshold exceeded: {metric_name} value {current_value} > {threshold}",
        "level": "WARNING",
        "description": "Business metric exceeded warning threshold"
    },
    "ANL_W005": {
        "code": "ANL_W005",
        "message": "Dashboard load time high: {dashboard_id} loaded in {load_time}ms",
        "level": "WARNING",
        "description": "Dashboard performance degradation"
    },
    "ANL_W006": {
        "code": "ANL_W006",
        "message": "Data staleness detected: {dataset_name} last updated {hours_ago}h ago",
        "level": "WARNING",
        "description": "Analytics data not recently refreshed"
    },
    "ANL_W007": {
        "code": "ANL_W007",
        "message": "Analytics service memory usage high: {memory_percentage}%",
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