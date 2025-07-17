from typing import Any, Dict, Optional

class DomainException(Exception):
    """Excepción base para errores de dominio"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

class BusinessRuleViolationException(DomainException):
    """Excepción para violaciones de reglas de negocio"""
    pass

class EntityNotFoundException(DomainException):
    """Excepción cuando no se encuentra una entidad"""
    
    def __init__(self, entity_type: str, entity_id: str, details: Dict[str, Any] = None):
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message, "ENTITY_NOT_FOUND", details)
        self.entity_type = entity_type
        self.entity_id = entity_id

class InvalidOperationException(DomainException):
    """Excepción para operaciones inválidas en el estado actual"""
    pass

class ValidationException(DomainException):
    """Excepción para errores de validación"""
    
    def __init__(self, field: str, value: Any, message: str, details: Dict[str, Any] = None):
        full_message = f"Validation error for field '{field}': {message}"
        super().__init__(full_message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value

class InsufficientFundsException(DomainException):
    """Excepción para fondos insuficientes"""
    
    def __init__(self, requested_amount: str, available_amount: str, details: Dict[str, Any] = None):
        message = f"Insufficient funds: requested {requested_amount}, available {available_amount}"
        super().__init__(message, "INSUFFICIENT_FUNDS", details)
        self.requested_amount = requested_amount
        self.available_amount = available_amount

class CreditLimitExceededException(DomainException):
    """Excepción para límite de crédito excedido"""
    
    def __init__(self, customer_id: str, limit: str, requested: str, details: Dict[str, Any] = None):
        message = f"Credit limit exceeded for customer {customer_id}: limit {limit}, requested {requested}"
        super().__init__(message, "CREDIT_LIMIT_EXCEEDED", details)
        self.customer_id = customer_id
        self.credit_limit = limit
        self.requested_amount = requested

class KYCRequiredException(DomainException):
    """Excepción cuando se requiere validación KYC"""
    
    def __init__(self, customer_id: str, operation: str, details: Dict[str, Any] = None):
        message = f"KYC validation required for customer {customer_id} to perform {operation}"
        super().__init__(message, "KYC_REQUIRED", details)
        self.customer_id = customer_id
        self.operation = operation

class ConcurrencyException(DomainException):
    """Excepción para problemas de concurrencia"""
    
    def __init__(self, entity_type: str, entity_id: str, details: Dict[str, Any] = None):
        message = f"Concurrency conflict detected for {entity_type} {entity_id}"
        super().__init__(message, "CONCURRENCY_CONFLICT", details)
        self.entity_type = entity_type
        self.entity_id = entity_id

class ExternalServiceException(DomainException):
    """Excepción para errores en servicios externos"""
    
    def __init__(self, service_name: str, operation: str, error_message: str, details: Dict[str, Any] = None):
        message = f"External service error in {service_name}.{operation}: {error_message}"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)
        self.service_name = service_name
        self.operation = operation

class PaymentException(DomainException):
    """Excepción para errores de pago"""
    
    def __init__(self, payment_method: str, amount: str, error_message: str, details: Dict[str, Any] = None):
        message = f"Payment failed: {payment_method} for amount {amount} - {error_message}"
        super().__init__(message, "PAYMENT_ERROR", details)
        self.payment_method = payment_method
        self.amount = amount

class ShippingException(DomainException):
    """Excepción para errores de envío"""
    
    def __init__(self, guide_id: str, operation: str, error_message: str, details: Dict[str, Any] = None):
        message = f"Shipping error for guide {guide_id} during {operation}: {error_message}"
        super().__init__(message, "SHIPPING_ERROR", details)
        self.guide_id = guide_id
        self.operation = operation

class FranchiseException(DomainException):
    """Excepción para errores de franquicia"""
    
    def __init__(self, franchise_id: str, operation: str, error_message: str, details: Dict[str, Any] = None):
        message = f"Franchise error for {franchise_id} during {operation}: {error_message}"
        super().__init__(message, "FRANCHISE_ERROR", details)
        self.franchise_id = franchise_id
        self.operation = operation

class TokenException(DomainException):
    """Excepción para errores de tokens"""
    
    def __init__(self, token_id: str, operation: str, error_message: str, details: Dict[str, Any] = None):
        message = f"Token error for {token_id} during {operation}: {error_message}"
        super().__init__(message, "TOKEN_ERROR", details)
        self.token_id = token_id
        self.operation = operation