from enum import Enum
from typing import Dict, Any

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCodes:
    # Customer related codes
    CUSTOMER_CREATED = "CUST_001"
    CUSTOMER_UPDATED = "CUST_002"
    CUSTOMER_KYC_VALIDATED = "CUST_003"
    CUSTOMER_DEACTIVATED = "CUST_004"
    CUSTOMER_NOT_FOUND = "CUST_E001"
    CUSTOMER_EMAIL_EXISTS = "CUST_E002"
    CUSTOMER_KYC_FAILED = "CUST_E003"
    
    # Order related codes
    ORDER_CREATED = "ORD_001"
    ORDER_QUOTED = "ORD_002"
    ORDER_CONFIRMED = "ORD_003"
    ORDER_CANCELLED = "ORD_004"
    ORDER_NOT_FOUND = "ORD_E001"
    ORDER_INVALID_STATUS = "ORD_E002"
    ORDER_KYC_REQUIRED = "ORD_E003"
    
    # Guide related codes
    GUIDE_GENERATED = "GDE_001"
    GUIDE_PICKED_UP = "GDE_002"
    GUIDE_IN_TRANSIT = "GDE_003"
    GUIDE_DELIVERED = "GDE_004"
    GUIDE_NOT_FOUND = "GDE_E001"
    GUIDE_INVALID_STATUS = "GDE_E002"
    
    # Payment related codes
    PAYMENT_PROCESSED = "PAY_001"
    PAYMENT_FAILED = "PAY_E001"
    PAYMENT_INSUFFICIENT_FUNDS = "PAY_E002"
    WALLET_CREDITED = "WAL_001"
    WALLET_DEBITED = "WAL_002"
    
    # System related codes
    DATABASE_CONNECTION_ERROR = "SYS_E001"
    EXTERNAL_SERVICE_ERROR = "SYS_E002"
    VALIDATION_ERROR = "SYS_E003"

LOG_MESSAGES: Dict[str, Dict[str, Any]] = {
    # Customer messages
    LogCodes.CUSTOMER_CREATED: {
        "level": LogLevel.INFO,
        "template": "Cliente creado exitosamente: {customer_id} - {email}",
        "description": "Un nuevo cliente ha sido registrado en el sistema"
    },
    LogCodes.CUSTOMER_UPDATED: {
        "level": LogLevel.INFO,
        "template": "Cliente actualizado: {customer_id} - Campos: {updated_fields}",
        "description": "Los datos del cliente han sido actualizados"
    },
    LogCodes.CUSTOMER_KYC_VALIDATED: {
        "level": LogLevel.INFO,
        "template": "KYC validado para cliente: {customer_id}",
        "description": "El proceso KYC del cliente ha sido completado exitosamente"
    },
    LogCodes.CUSTOMER_DEACTIVATED: {
        "level": LogLevel.WARNING,
        "template": "Cliente desactivado: {customer_id} - Razón: {reason}",
        "description": "Un cliente ha sido desactivado en el sistema"
    },
    LogCodes.CUSTOMER_NOT_FOUND: {
        "level": LogLevel.ERROR,
        "template": "Cliente no encontrado: {customer_id}",
        "description": "Se intentó acceder a un cliente que no existe"
    },
    LogCodes.CUSTOMER_EMAIL_EXISTS: {
        "level": LogLevel.ERROR,
        "template": "Email ya registrado: {email}",
        "description": "Se intentó registrar un cliente con un email ya existente"
    },
    LogCodes.CUSTOMER_KYC_FAILED: {
        "level": LogLevel.ERROR,
        "template": "Validación KYC fallida para cliente: {customer_id} - Razón: {reason}",
        "description": "El proceso de validación KYC ha fallado"
    },
    
    # Order messages
    LogCodes.ORDER_CREATED: {
        "level": LogLevel.INFO,
        "template": "Orden creada: {order_id} - Cliente: {customer_id} - Destino: {destination}",
        "description": "Una nueva orden de envío ha sido creada"
    },
    LogCodes.ORDER_QUOTED: {
        "level": LogLevel.INFO,
        "template": "Orden cotizada: {order_id} - Precio: ${price} - Días estimados: {delivery_days}",
        "description": "Se ha generado una cotización para la orden"
    },
    LogCodes.ORDER_CONFIRMED: {
        "level": LogLevel.INFO,
        "template": "Orden confirmada: {order_id} - Cliente: {customer_id}",
        "description": "Una orden ha sido confirmada por el cliente"
    },
    LogCodes.ORDER_CANCELLED: {
        "level": LogLevel.WARNING,
        "template": "Orden cancelada: {order_id} - Razón: {reason}",
        "description": "Una orden ha sido cancelada"
    },
    LogCodes.ORDER_NOT_FOUND: {
        "level": LogLevel.ERROR,
        "template": "Orden no encontrada: {order_id}",
        "description": "Se intentó acceder a una orden que no existe"
    },
    LogCodes.ORDER_INVALID_STATUS: {
        "level": LogLevel.ERROR,
        "template": "Estado de orden inválido: {order_id} - Estado actual: {current_status} - Acción: {action}",
        "description": "Se intentó realizar una acción inválida según el estado de la orden"
    },
    LogCodes.ORDER_KYC_REQUIRED: {
        "level": LogLevel.ERROR,
        "template": "KYC requerido para orden internacional: {order_id} - Cliente: {customer_id}",
        "description": "Se requiere validación KYC para crear un envío internacional"
    },
    
    # Guide messages
    LogCodes.GUIDE_GENERATED: {
        "level": LogLevel.INFO,
        "template": "Guía generada: {guide_id} - Orden: {order_id} - Operador: {operator}",
        "description": "Se ha generado una nueva guía de envío"
    },
    LogCodes.GUIDE_PICKED_UP: {
        "level": LogLevel.INFO,
        "template": "Paquete recolectado: {guide_id} - Ubicación: {location}",
        "description": "El paquete ha sido recolectado"
    },
    LogCodes.GUIDE_IN_TRANSIT: {
        "level": LogLevel.INFO,
        "template": "Paquete en tránsito: {guide_id} - Ubicación actual: {location}",
        "description": "El paquete está en tránsito"
    },
    LogCodes.GUIDE_DELIVERED: {
        "level": LogLevel.INFO,
        "template": "Paquete entregado: {guide_id} - Receptor: {recipient} - Fecha: {delivery_date}",
        "description": "El paquete ha sido entregado exitosamente"
    },
    LogCodes.GUIDE_NOT_FOUND: {
        "level": LogLevel.ERROR,
        "template": "Guía no encontrada: {guide_id}",
        "description": "Se intentó acceder a una guía que no existe"
    },
    LogCodes.GUIDE_INVALID_STATUS: {
        "level": LogLevel.ERROR,
        "template": "Estado de guía inválido: {guide_id} - Estado actual: {current_status} - Acción: {action}",
        "description": "Se intentó realizar una acción inválida según el estado de la guía"
    },
    
    # Payment messages
    LogCodes.PAYMENT_PROCESSED: {
        "level": LogLevel.INFO,
        "template": "Pago procesado: {transaction_id} - Monto: ${amount} - Método: {method}",
        "description": "Un pago ha sido procesado exitosamente"
    },
    LogCodes.PAYMENT_FAILED: {
        "level": LogLevel.ERROR,
        "template": "Pago fallido: {transaction_id} - Monto: ${amount} - Error: {error}",
        "description": "Un pago ha fallado"
    },
    LogCodes.PAYMENT_INSUFFICIENT_FUNDS: {
        "level": LogLevel.ERROR,
        "template": "Fondos insuficientes: Cliente: {customer_id} - Monto solicitado: ${amount} - Disponible: ${available}",
        "description": "El cliente no tiene fondos suficientes para la transacción"
    },
    LogCodes.WALLET_CREDITED: {
        "level": LogLevel.INFO,
        "template": "Wallet acreditado: {wallet_id} - Monto: ${amount} - Nuevo balance: ${balance}",
        "description": "Se han agregado fondos al wallet del cliente"
    },
    LogCodes.WALLET_DEBITED: {
        "level": LogLevel.INFO,
        "template": "Wallet debitado: {wallet_id} - Monto: ${amount} - Nuevo balance: ${balance}",
        "description": "Se han debitado fondos del wallet del cliente"
    },
    
    # System messages
    LogCodes.DATABASE_CONNECTION_ERROR: {
        "level": LogLevel.CRITICAL,
        "template": "Error de conexión a base de datos: {error}",
        "description": "Fallo en la conexión a la base de datos"
    },
    LogCodes.EXTERNAL_SERVICE_ERROR: {
        "level": LogLevel.ERROR,
        "template": "Error en servicio externo: {service} - Error: {error}",
        "description": "Fallo en la comunicación con un servicio externo"
    },
    LogCodes.VALIDATION_ERROR: {
        "level": LogLevel.ERROR,
        "template": "Error de validación: {field} - Valor: {value} - Error: {error}",
        "description": "Error en la validación de datos de entrada"
    }
}

def get_log_message(code: str, **kwargs) -> Dict[str, Any]:
    """
    Obtiene el mensaje de log formateado para un código específico
    """
    if code not in LOG_MESSAGES:
        return {
            "level": LogLevel.ERROR,
            "message": f"Código de log desconocido: {code}",
            "description": "Mensaje de log no encontrado"
        }
    
    log_config = LOG_MESSAGES[code]
    try:
        formatted_message = log_config["template"].format(**kwargs)
    except KeyError as e:
        formatted_message = f"Error formateando mensaje {code}: parámetro faltante {e}"
    
    return {
        "code": code,
        "level": log_config["level"],
        "message": formatted_message,
        "description": log_config["description"],
        "context": kwargs
    }