"""
Shared Service Logger Configuration
Common logging setup for all Quenty microservices
"""

import structlog
import logging
import os
from typing import Dict, Any

def setup_service_logger(service_name: str, log_messages: Dict[str, Any] = None):
    """
    Setup structured logging for a microservice
    
    Args:
        service_name: Name of the microservice (e.g., 'auth-service')
        log_messages: Dictionary of log messages for the service
    
    Returns:
        Configured logger instance
    """
    
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Create service-specific logger
    logger = structlog.get_logger(service_name)
    
    return logger

def log_startup(logger, service_name: str, port: int, log_messages: Dict[str, Any] = None):
    """Log service startup with structured message"""
    if log_messages and "INFO_MESSAGES" in log_messages:
        # Try to find startup message pattern
        startup_keys = [k for k in log_messages["INFO_MESSAGES"].keys() if "started" in log_messages["INFO_MESSAGES"][k]["message"].lower()]
        if startup_keys:
            startup_msg = log_messages["INFO_MESSAGES"][startup_keys[0]]
            logger.info(
                startup_msg["message"].format(port=port),
                **startup_msg
            )
            return
    
    # Fallback generic message
    logger.info(f"{service_name} started successfully on port {port}")

def log_error(logger, error_code: str, error_details: str = "", log_messages: Dict[str, Any] = None, **kwargs):
    """Log error with structured message"""
    if log_messages and "ERROR_MESSAGES" in log_messages and error_code in log_messages["ERROR_MESSAGES"]:
        error_msg = log_messages["ERROR_MESSAGES"][error_code]
        logger.error(
            error_msg["message"].format(**kwargs) if kwargs else error_msg["message"],
            **error_msg,
            error_details=error_details
        )
    else:
        logger.error(f"Error {error_code}: {error_details}")

def log_info(logger, info_code: str, log_messages: Dict[str, Any] = None, **kwargs):
    """Log info with structured message"""
    if log_messages and "INFO_MESSAGES" in log_messages and info_code in log_messages["INFO_MESSAGES"]:
        info_msg = log_messages["INFO_MESSAGES"][info_code]
        logger.info(
            info_msg["message"].format(**kwargs) if kwargs else info_msg["message"],
            **info_msg
        )
    else:
        logger.info(f"Info {info_code}")

def log_warning(logger, warning_code: str, log_messages: Dict[str, Any] = None, **kwargs):
    """Log warning with structured message"""
    if log_messages and "WARNING_MESSAGES" in log_messages and warning_code in log_messages["WARNING_MESSAGES"]:
        warning_msg = log_messages["WARNING_MESSAGES"][warning_code]
        logger.warning(
            warning_msg["message"].format(**kwargs) if kwargs else warning_msg["message"],
            **warning_msg
        )
    else:
        logger.warning(f"Warning {warning_code}")

def log_debug(logger, debug_code: str, log_messages: Dict[str, Any] = None, **kwargs):
    """Log debug with structured message"""
    if log_messages and "DEBUG_MESSAGES" in log_messages and debug_code in log_messages["DEBUG_MESSAGES"]:
        debug_msg = log_messages["DEBUG_MESSAGES"][debug_code]
        logger.debug(
            debug_msg["message"].format(**kwargs) if kwargs else debug_msg["message"],
            **debug_msg
        )
    else:
        logger.debug(f"Debug {debug_code}")

# Database operation logging helper
def log_db_operation(logger, operation_type: str, execution_time_ms: int, log_messages: Dict[str, Any] = None, **kwargs):
    """Log database operation with performance metrics"""
    if execution_time_ms > 1000:  # Log warning for slow queries
        log_warning(logger, "DB_W001", log_messages, 
                   operation_type=operation_type, 
                   execution_time=execution_time_ms, **kwargs)
    else:
        log_debug(logger, "DB_D001", log_messages,
                 operation_type=operation_type, 
                 execution_time=execution_time_ms, **kwargs)

# Request processing logging helper
def log_request(logger, request_type: str, request_id: str = None, log_messages: Dict[str, Any] = None, **kwargs):
    """Log request processing"""
    log_debug(logger, "REQ_D001", log_messages,
             request_type=request_type,
             request_id=request_id or "unknown", **kwargs)