from typing import Dict, Any, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()


class CarrierErrorType(Enum):
    AUTHENTICATION = "authentication_error"
    RATE_LIMIT = "rate_limit_exceeded"
    INVALID_ADDRESS = "invalid_address"
    INVALID_PACKAGE = "invalid_package_dimensions"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_TRACKING = "invalid_tracking_number"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    COVERAGE_UNAVAILABLE = "no_coverage_available"
    CUSTOMS_REQUIRED = "customs_documentation_required"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "request_timeout"
    UNKNOWN = "unknown_error"


class CarrierException(Exception):
    """Base exception for carrier-related errors"""
    
    def __init__(
        self,
        carrier: str,
        error_type: CarrierErrorType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        self.carrier = carrier
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.retry_after = retry_after
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "carrier": self.carrier,
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "retry_after": self.retry_after
        }


class DHLErrorHandler:
    """Error handler for DHL specific errors"""
    
    @staticmethod
    def handle_error(error_response: Dict[str, Any]) -> CarrierException:
        error_code = error_response.get('code', '')
        error_message = error_response.get('message', 'Unknown DHL error')
        
        error_mapping = {
            '401': CarrierErrorType.AUTHENTICATION,
            '403': CarrierErrorType.AUTHENTICATION,
            '429': CarrierErrorType.RATE_LIMIT,
            '400': CarrierErrorType.INVALID_PACKAGE,
            '404': CarrierErrorType.INVALID_TRACKING,
            '503': CarrierErrorType.SERVICE_UNAVAILABLE,
            'INVALID_POSTAL_CODE': CarrierErrorType.INVALID_ADDRESS,
            'NO_SERVICE_AVAILABLE': CarrierErrorType.COVERAGE_UNAVAILABLE,
            'CUSTOMS_REQUIRED': CarrierErrorType.CUSTOMS_REQUIRED
        }
        
        error_type = error_mapping.get(str(error_code), CarrierErrorType.UNKNOWN)
        
        # Extract retry-after header if rate limited
        retry_after = None
        if error_type == CarrierErrorType.RATE_LIMIT:
            retry_after = error_response.get('retry_after', 60)
        
        logger.error("DHL API error", 
                    error_code=error_code,
                    error_type=error_type.value,
                    message=error_message)
        
        return CarrierException(
            carrier="DHL",
            error_type=error_type,
            message=error_message,
            details=error_response,
            retry_after=retry_after
        )


class FedExErrorHandler:
    """Error handler for FedEx specific errors"""
    
    @staticmethod
    def handle_error(error_response: Dict[str, Any]) -> CarrierException:
        errors = error_response.get('errors', [])
        if not errors:
            return CarrierException(
                carrier="FedEx",
                error_type=CarrierErrorType.UNKNOWN,
                message="Unknown FedEx error",
                details=error_response
            )
        
        first_error = errors[0]
        error_code = first_error.get('code', '')
        error_message = first_error.get('message', 'Unknown FedEx error')
        
        error_mapping = {
            'UNAUTHORIZED': CarrierErrorType.AUTHENTICATION,
            'FORBIDDEN': CarrierErrorType.AUTHENTICATION,
            'RATE.LIMIT.EXCEEDED': CarrierErrorType.RATE_LIMIT,
            'INVALID.INPUT': CarrierErrorType.INVALID_PACKAGE,
            'TRACKING.NUMBER.NOT.FOUND': CarrierErrorType.INVALID_TRACKING,
            'SERVICE.UNAVAILABLE': CarrierErrorType.SERVICE_UNAVAILABLE,
            'INVALID.POSTAL.CODE': CarrierErrorType.INVALID_ADDRESS,
            'SERVICE.NOT.AVAILABLE': CarrierErrorType.COVERAGE_UNAVAILABLE,
            'CUSTOMS.DOCUMENTATION.REQUIRED': CarrierErrorType.CUSTOMS_REQUIRED,
            'INSUFFICIENT.FUNDS': CarrierErrorType.INSUFFICIENT_FUNDS
        }
        
        error_type = error_mapping.get(error_code, CarrierErrorType.UNKNOWN)
        
        logger.error("FedEx API error",
                    error_code=error_code,
                    error_type=error_type.value,
                    message=error_message)
        
        return CarrierException(
            carrier="FedEx",
            error_type=error_type,
            message=error_message,
            details={"errors": errors}
        )


class UPSErrorHandler:
    """Error handler for UPS specific errors"""
    
    @staticmethod
    def handle_error(error_response: Dict[str, Any]) -> CarrierException:
        response = error_response.get('response', {})
        errors = response.get('errors', [])
        
        if not errors:
            return CarrierException(
                carrier="UPS",
                error_type=CarrierErrorType.UNKNOWN,
                message="Unknown UPS error",
                details=error_response
            )
        
        first_error = errors[0]
        error_code = first_error.get('code', '')
        error_message = first_error.get('message', 'Unknown UPS error')
        
        error_mapping = {
            '250002': CarrierErrorType.AUTHENTICATION,
            '250003': CarrierErrorType.AUTHENTICATION,
            '250004': CarrierErrorType.RATE_LIMIT,
            '120100': CarrierErrorType.INVALID_ADDRESS,
            '120101': CarrierErrorType.INVALID_ADDRESS,
            '120102': CarrierErrorType.INVALID_PACKAGE,
            '120103': CarrierErrorType.INVALID_PACKAGE,
            '151018': CarrierErrorType.INVALID_TRACKING,
            '9999999': CarrierErrorType.SERVICE_UNAVAILABLE,
            '120900': CarrierErrorType.COVERAGE_UNAVAILABLE,
            '120124': CarrierErrorType.CUSTOMS_REQUIRED
        }
        
        error_type = error_mapping.get(error_code, CarrierErrorType.UNKNOWN)
        
        logger.error("UPS API error",
                    error_code=error_code,
                    error_type=error_type.value,
                    message=error_message)
        
        return CarrierException(
            carrier="UPS",
            error_type=error_type,
            message=error_message,
            details={"errors": errors}
        )


class ServientregaErrorHandler:
    """Error handler for Servientrega specific errors"""
    
    @staticmethod
    def handle_error(error_response: Dict[str, Any]) -> CarrierException:
        error_code = error_response.get('Codigo', '')
        error_message = error_response.get('Mensaje', 'Error en Servientrega')
        
        error_mapping = {
            'AUTH001': CarrierErrorType.AUTHENTICATION,
            'AUTH002': CarrierErrorType.AUTHENTICATION,
            'LIM001': CarrierErrorType.RATE_LIMIT,
            'DIR001': CarrierErrorType.INVALID_ADDRESS,
            'DIR002': CarrierErrorType.INVALID_ADDRESS,
            'PAQ001': CarrierErrorType.INVALID_PACKAGE,
            'GUI001': CarrierErrorType.INVALID_TRACKING,
            'SRV001': CarrierErrorType.SERVICE_UNAVAILABLE,
            'COB001': CarrierErrorType.COVERAGE_UNAVAILABLE,
            'COB002': CarrierErrorType.COVERAGE_UNAVAILABLE,
            'SAL001': CarrierErrorType.INSUFFICIENT_FUNDS
        }
        
        error_type = error_mapping.get(error_code, CarrierErrorType.UNKNOWN)
        
        logger.error("Servientrega API error",
                    error_code=error_code,
                    error_type=error_type.value,
                    message=error_message)
        
        return CarrierException(
            carrier="Servientrega",
            error_type=error_type,
            message=error_message,
            details=error_response
        )


class InterrapidisimoErrorHandler:
    """Error handler for Interrapidisimo specific errors"""
    
    @staticmethod
    def handle_error(error_response: Dict[str, Any]) -> CarrierException:
        error = error_response.get('error', {})
        error_code = error.get('code', '')
        error_message = error.get('message', 'Error en Interrapidisimo')
        
        error_mapping = {
            'UNAUTHORIZED': CarrierErrorType.AUTHENTICATION,
            'FORBIDDEN': CarrierErrorType.AUTHENTICATION,
            'RATE_LIMIT': CarrierErrorType.RATE_LIMIT,
            'INVALID_ADDRESS': CarrierErrorType.INVALID_ADDRESS,
            'INVALID_PACKAGE': CarrierErrorType.INVALID_PACKAGE,
            'TRACKING_NOT_FOUND': CarrierErrorType.INVALID_TRACKING,
            'SERVICE_UNAVAILABLE': CarrierErrorType.SERVICE_UNAVAILABLE,
            'NO_COVERAGE': CarrierErrorType.COVERAGE_UNAVAILABLE,
            'INSUFFICIENT_BALANCE': CarrierErrorType.INSUFFICIENT_FUNDS
        }
        
        error_type = error_mapping.get(error_code, CarrierErrorType.UNKNOWN)
        
        logger.error("Interrapidisimo API error",
                    error_code=error_code,
                    error_type=error_type.value,
                    message=error_message)
        
        return CarrierException(
            carrier="Interrapidisimo",
            error_type=error_type,
            message=error_message,
            details=error_response
        )


# Aliases for backward compatibility
CarrierError = CarrierException
ValidationError = CarrierException
AuthenticationError = CarrierException


class ErrorHandlerFactory:
    """Factory to get appropriate error handler for each carrier"""
    
    _handlers = {
        "DHL": DHLErrorHandler,
        "FedEx": FedExErrorHandler,
        "UPS": UPSErrorHandler,
        "Servientrega": ServientregaErrorHandler,
        "Interrapidisimo": InterrapidisimoErrorHandler
    }
    
    @classmethod
    def get_handler(cls, carrier: str):
        """Get error handler for specific carrier"""
        handler_class = cls._handlers.get(carrier)
        if not handler_class:
            logger.warning(f"No specific error handler for carrier {carrier}")
            return None
        return handler_class()
    
    @classmethod
    def handle_error(cls, carrier: str, error_response: Dict[str, Any]) -> CarrierException:
        """Handle error for specific carrier"""
        handler = cls.get_handler(carrier)
        if handler:
            return handler.handle_error(error_response)
        
        # Generic error if no handler found
        return CarrierException(
            carrier=carrier,
            error_type=CarrierErrorType.UNKNOWN,
            message="Unknown carrier error",
            details=error_response
        )