from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Union, Dict, Any
import traceback
from src.domain.exceptions.base_exceptions import *
from src.infrastructure.logging.logger import logger, log_database_error
from src.infrastructure.logging.log_messages import LogCodes

class ErrorHandler:
    """Manejador centralizado de errores"""
    
    @staticmethod
    async def handle_domain_exception(request: Request, exc: DomainException) -> JSONResponse:
        """Maneja excepciones de dominio"""
        
        # Log del error
        logger.log_with_code(
            LogCodes.VALIDATION_ERROR,
            field="domain",
            value=exc.error_code,
            error=exc.message
        )
        
        # Mapear a código HTTP apropiado
        status_code = ErrorHandler._get_http_status_for_domain_exception(exc)
        
        response_data = {
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            }
        }
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    async def handle_validation_exception(request: Request, exc: ValidationException) -> JSONResponse:
        """Maneja excepciones de validación específicamente"""
        
        logger.log_with_code(
            LogCodes.VALIDATION_ERROR,
            field=exc.field,
            value=str(exc.value),
            error=exc.message
        )
        
        response_data = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "field": exc.field,
                "value": exc.value,
                "details": exc.details
            }
        }
        
        return JSONResponse(status_code=422, content=response_data)
    
    @staticmethod
    async def handle_entity_not_found(request: Request, exc: EntityNotFoundException) -> JSONResponse:
        """Maneja excepciones de entidad no encontrada"""
        
        logger.log_with_code(
            LogCodes.CUSTOMER_NOT_FOUND if exc.entity_type == "Customer" else "ENTITY_NOT_FOUND",
            customer_id=exc.entity_id if exc.entity_type == "Customer" else exc.entity_id
        )
        
        response_data = {
            "error": {
                "code": "ENTITY_NOT_FOUND",
                "message": exc.message,
                "entity_type": exc.entity_type,
                "entity_id": exc.entity_id
            }
        }
        
        return JSONResponse(status_code=404, content=response_data)
    
    @staticmethod
    async def handle_business_rule_violation(request: Request, exc: BusinessRuleViolationException) -> JSONResponse:
        """Maneja violaciones de reglas de negocio"""
        
        logger.error(
            f"Business rule violation: {exc.message}",
            error_code=exc.error_code,
            details=exc.details
        )
        
        response_data = {
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "type": "BUSINESS_RULE_VIOLATION",
                "details": exc.details
            }
        }
        
        return JSONResponse(status_code=400, content=response_data)
    
    @staticmethod
    async def handle_insufficient_funds(request: Request, exc: InsufficientFundsException) -> JSONResponse:
        """Maneja errores de fondos insuficientes"""
        
        logger.log_with_code(
            LogCodes.PAYMENT_INSUFFICIENT_FUNDS,
            customer_id=exc.details.get("customer_id", "unknown"),
            amount=exc.requested_amount,
            available=exc.available_amount
        )
        
        response_data = {
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": exc.message,
                "requested_amount": exc.requested_amount,
                "available_amount": exc.available_amount
            }
        }
        
        return JSONResponse(status_code=402, content=response_data)
    
    @staticmethod
    async def handle_external_service_error(request: Request, exc: ExternalServiceException) -> JSONResponse:
        """Maneja errores de servicios externos"""
        
        logger.log_with_code(
            LogCodes.EXTERNAL_SERVICE_ERROR,
            service=exc.service_name,
            error=exc.message
        )
        
        response_data = {
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": "External service temporarily unavailable",
                "service": exc.service_name,
                "operation": exc.operation
            }
        }
        
        return JSONResponse(status_code=503, content=response_data)
    
    @staticmethod
    async def handle_database_error(request: Request, exc: Exception) -> JSONResponse:
        """Maneja errores de base de datos"""
        
        log_database_error(str(exc))
        
        response_data = {
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "type": "INTERNAL_ERROR"
            }
        }
        
        return JSONResponse(status_code=500, content=response_data)
    
    @staticmethod
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """Maneja excepciones genéricas no controladas"""
        
        # Log completo del error incluyendo stack trace
        logger.critical(
            f"Unhandled exception: {str(exc)}",
            exception_type=exc.__class__.__name__,
            traceback=traceback.format_exc()
        )
        
        response_data = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "type": "INTERNAL_ERROR"
            }
        }
        
        return JSONResponse(status_code=500, content=response_data)
    
    @staticmethod
    def _get_http_status_for_domain_exception(exc: DomainException) -> int:
        """Mapea excepciones de dominio a códigos HTTP"""
        
        status_mapping = {
            EntityNotFoundException: 404,
            ValidationException: 422,
            BusinessRuleViolationException: 400,
            InvalidOperationException: 400,
            InsufficientFundsException: 402,
            CreditLimitExceededException: 402,
            KYCRequiredException: 403,
            PaymentException: 402,
            ExternalServiceException: 503,
            ConcurrencyException: 409
        }
        
        return status_mapping.get(type(exc), 400)

# Función para registrar todos los manejadores de errores
def register_error_handlers(app):
    """Registra todos los manejadores de errores en la aplicación FastAPI"""
    
    # Manejadores específicos de dominio
    app.add_exception_handler(DomainException, ErrorHandler.handle_domain_exception)
    app.add_exception_handler(ValidationException, ErrorHandler.handle_validation_exception)
    app.add_exception_handler(EntityNotFoundException, ErrorHandler.handle_entity_not_found)
    app.add_exception_handler(BusinessRuleViolationException, ErrorHandler.handle_business_rule_violation)
    app.add_exception_handler(InsufficientFundsException, ErrorHandler.handle_insufficient_funds)
    app.add_exception_handler(ExternalServiceException, ErrorHandler.handle_external_service_error)
    
    # Manejadores para errores de infraestructura
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Verificar si es un error de base de datos
        if "database" in str(exc).lower() or "connection" in str(exc).lower():
            return await ErrorHandler.handle_database_error(request, exc)
        
        return await ErrorHandler.handle_generic_exception(request, exc)
    
    # Mantener el manejador por defecto para HTTPException
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await http_exception_handler(request, exc)

class ErrorContext:
    """Contexto para manejo de errores con información adicional"""
    
    def __init__(self, operation: str, entity_type: str = None, entity_id: str = None):
        self.operation = operation
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.additional_context = {}
    
    def add_context(self, key: str, value: Any) -> "ErrorContext":
        """Agrega contexto adicional"""
        self.additional_context[key] = value
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a diccionario"""
        return {
            "operation": self.operation,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            **self.additional_context
        }