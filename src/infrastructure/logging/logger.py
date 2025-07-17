import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from src.infrastructure.logging.log_messages import get_log_message, LogLevel

class QuantyLogger:
    """
    Logger personalizado para la plataforma Quenty
    """
    
    def __init__(self, name: str = "quenty"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura el logger con formato JSON estructurado"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = JsonFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
    
    def log_with_code(self, code: str, **kwargs):
        """Registra un log usando un código predefinido"""
        log_data = get_log_message(code, **kwargs)
        
        level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        log_level = level_mapping.get(log_data["level"], logging.INFO)
        
        extra_data = {
            "code": log_data["code"],
            "description": log_data["description"],
            "context": log_data.get("context", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.log(log_level, log_data["message"], extra=extra_data)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self._log_custom(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de información"""
        self._log_custom(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de advertencia"""
        self._log_custom(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de error"""
        self._log_custom(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico"""
        self._log_custom(logging.CRITICAL, message, **kwargs)
    
    def _log_custom(self, level: int, message: str, **kwargs):
        """Registra un log personalizado"""
        extra_data = {
            "context": kwargs,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.log(level, message, extra=extra_data)

class JsonFormatter(logging.Formatter):
    """Formateador JSON para logs estructurados"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar información extra si está disponible
        if hasattr(record, 'code'):
            log_entry["code"] = record.code
        
        if hasattr(record, 'description'):
            log_entry["description"] = record.description
        
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

# Instancia global del logger
logger = QuantyLogger()

# Funciones de conveniencia para usar en toda la aplicación
def log_customer_created(customer_id: str, email: str):
    """Log para creación de cliente"""
    from src.infrastructure.logging.log_messages import LogCodes
    logger.log_with_code(LogCodes.CUSTOMER_CREATED, customer_id=customer_id, email=email)

def log_customer_not_found(customer_id: str):
    """Log para cliente no encontrado"""
    from src.infrastructure.logging.log_messages import LogCodes
    logger.log_with_code(LogCodes.CUSTOMER_NOT_FOUND, customer_id=customer_id)

def log_order_created(order_id: str, customer_id: str, destination: str):
    """Log para creación de orden"""
    from src.infrastructure.logging.log_messages import LogCodes
    logger.log_with_code(LogCodes.ORDER_CREATED, 
                        order_id=order_id, 
                        customer_id=customer_id, 
                        destination=destination)

def log_payment_processed(transaction_id: str, amount: str, method: str):
    """Log para pago procesado"""
    from src.infrastructure.logging.log_messages import LogCodes
    logger.log_with_code(LogCodes.PAYMENT_PROCESSED, 
                        transaction_id=transaction_id, 
                        amount=amount, 
                        method=method)

def log_database_error(error: str):
    """Log para errores de base de datos"""
    from src.infrastructure.logging.log_messages import LogCodes
    logger.log_with_code(LogCodes.DATABASE_CONNECTION_ERROR, error=error)