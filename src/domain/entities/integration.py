from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import json


class ChannelType(Enum):
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MERCADOLIBRE = "mercadolibre"
    MAGENTO = "magento"
    PRESTASHOP = "prestashop"
    CUSTOM_API = "custom_api"
    WEBHOOK = "webhook"


class IntegrationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


class AuthType(Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    JWT = "jwt"
    WEBHOOK_SECRET = "webhook_secret"


@dataclass
class AuthConfig:
    auth_type: AuthType
    credentials: Dict[str, str]  # API keys, tokens, etc.
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class WebhookConfig:
    url: str
    secret: str
    events: List[str]
    retry_attempts: int = 3
    timeout_seconds: int = 30


@dataclass
class FieldMapping:
    source_field: str
    target_field: str
    transformation: Optional[str] = None  # JSON transformation rule
    is_required: bool = True


@dataclass
class IntegrationEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    status: str  # "success", "failed", "retrying"
    error_message: Optional[str] = None
    retry_count: int = 0


class SalesChannelIntegration:
    def __init__(
        self,
        integration_id: str,
        customer_id: str,
        channel_type: ChannelType,
        channel_name: str
    ):
        self.integration_id = integration_id
        self.customer_id = customer_id
        self.channel_type = channel_type
        self.channel_name = channel_name
        self.status = IntegrationStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.last_sync_at: Optional[datetime] = None
        self.auth_config: Optional[AuthConfig] = None
        self.webhook_config: Optional[WebhookConfig] = None
        self.field_mappings: List[FieldMapping] = []
        self.sync_frequency_minutes: int = 15  # Default sync frequency
        self.auto_create_orders: bool = True
        self.auto_update_tracking: bool = True
        self.filter_rules: Dict[str, Any] = {}  # Rules to filter which orders to sync
        self.last_error: Optional[str] = None
        self.total_orders_synced: int = 0
        self.failed_sync_attempts: int = 0

    def configure_auth(self, auth_config: AuthConfig) -> None:
        """Configurar autenticación para la integración"""
        self.auth_config = auth_config
        self.updated_at = datetime.now()

    def configure_webhook(self, webhook_config: WebhookConfig) -> None:
        """Configurar webhook para recibir eventos del canal"""
        self.webhook_config = webhook_config
        self.updated_at = datetime.now()

    def add_field_mapping(self, mapping: FieldMapping) -> None:
        """Agregar mapeo de campos"""
        # Remover mapeo existente para el mismo campo fuente
        self.field_mappings = [m for m in self.field_mappings if m.source_field != mapping.source_field]
        self.field_mappings.append(mapping)
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activar integración después de configuración"""
        if not self.auth_config:
            raise ValueError("Se requiere configuración de autenticación")
        
        if not self.field_mappings:
            raise ValueError("Se requiere al menos un mapeo de campos")
        
        self.status = IntegrationStatus.ACTIVE
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Desactivar integración"""
        self.status = IntegrationStatus.INACTIVE
        self.updated_at = datetime.now()

    def suspend(self, reason: str) -> None:
        """Suspender integración por error"""
        self.status = IntegrationStatus.SUSPENDED
        self.last_error = reason
        self.updated_at = datetime.now()

    def record_sync_success(self, orders_processed: int) -> None:
        """Registrar sincronización exitosa"""
        self.last_sync_at = datetime.now()
        self.total_orders_synced += orders_processed
        self.failed_sync_attempts = 0
        self.last_error = None
        self.updated_at = datetime.now()

    def record_sync_failure(self, error_message: str) -> None:
        """Registrar falla en sincronización"""
        self.failed_sync_attempts += 1
        self.last_error = error_message
        self.updated_at = datetime.now()
        
        # Suspender si hay muchos fallos consecutivos
        if self.failed_sync_attempts >= 5:
            self.suspend(f"Suspendido por {self.failed_sync_attempts} fallos consecutivos")

    def set_filter_rules(self, rules: Dict[str, Any]) -> None:
        """Configurar reglas de filtrado de órdenes"""
        self.filter_rules = rules
        self.updated_at = datetime.now()

    def should_sync_order(self, order_data: Dict[str, Any]) -> bool:
        """Verificar si una orden debe ser sincronizada según las reglas de filtro"""
        if not self.filter_rules:
            return True
        
        # Implementar lógica de filtrado según reglas configuradas
        # Por simplicidad, asumimos que todas las órdenes se sincronizan
        return True

    def transform_order_data(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformar datos de orden usando los mapeos configurados"""
        transformed_data = {}
        
        for mapping in self.field_mappings:
            source_value = source_data.get(mapping.source_field)
            
            if source_value is None and mapping.is_required:
                raise ValueError(f"Campo requerido {mapping.source_field} no encontrado")
            
            if source_value is not None:
                # Aplicar transformación si está definida
                if mapping.transformation:
                    # Aquí iría la lógica de transformación
                    # Por simplicidad, solo copiamos el valor
                    transformed_value = source_value
                else:
                    transformed_value = source_value
                
                transformed_data[mapping.target_field] = transformed_value
        
        return transformed_data

    def is_auth_valid(self) -> bool:
        """Verificar si la autenticación es válida"""
        if not self.auth_config:
            return False
        
        if self.auth_config.expires_at and self.auth_config.expires_at <= datetime.now():
            return False
        
        return True

    def get_sync_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de sincronización"""
        return {
            "total_orders_synced": self.total_orders_synced,
            "failed_sync_attempts": self.failed_sync_attempts,
            "last_sync_at": self.last_sync_at,
            "last_error": self.last_error,
            "status": self.status.value,
            "uptime_percentage": self._calculate_uptime_percentage()
        }

    def _calculate_uptime_percentage(self) -> float:
        """Calcular porcentaje de tiempo activo"""
        # Implementación simplificada
        if self.status == IntegrationStatus.ACTIVE:
            return 100.0
        elif self.status == IntegrationStatus.ERROR:
            return 50.0
        else:
            return 0.0


class WebhookEndpoint:
    def __init__(
        self,
        endpoint_id: str,
        integration_id: str,
        event_type: str,
        url: str
    ):
        self.endpoint_id = endpoint_id
        self.integration_id = integration_id
        self.event_type = event_type
        self.url = url
        self.secret: Optional[str] = None
        self.is_active = True
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.last_triggered_at: Optional[datetime] = None
        self.total_triggers: int = 0
        self.failed_triggers: int = 0
        self.events_history: List[IntegrationEvent] = []

    def set_secret(self, secret: str) -> None:
        """Configurar secreto para validar webhooks"""
        self.secret = secret
        self.updated_at = datetime.now()

    def trigger(self, data: Dict[str, Any]) -> IntegrationEvent:
        """Disparar webhook con datos"""
        event = IntegrationEvent(
            event_id=f"evt_{datetime.now().timestamp()}",
            event_type=self.event_type,
            timestamp=datetime.now(),
            data=data,
            status="pending"
        )
        
        self.events_history.append(event)
        self.total_triggers += 1
        self.last_triggered_at = datetime.now()
        
        return event

    def record_success(self, event_id: str) -> None:
        """Registrar éxito en el disparo del webhook"""
        event = next((e for e in self.events_history if e.event_id == event_id), None)
        if event:
            event.status = "success"

    def record_failure(self, event_id: str, error_message: str) -> None:
        """Registrar falla en el disparo del webhook"""
        event = next((e for e in self.events_history if e.event_id == event_id), None)
        if event:
            event.status = "failed"
            event.error_message = error_message
            self.failed_triggers += 1

    def get_recent_events(self, limit: int = 50) -> List[IntegrationEvent]:
        """Obtener eventos recientes"""
        return sorted(self.events_history, key=lambda e: e.timestamp, reverse=True)[:limit]


class NotificationTemplate:
    def __init__(
        self,
        template_id: str,
        name: str,
        channel: str,  # "email", "sms", "whatsapp", "push"
        event_type: str
    ):
        self.template_id = template_id
        self.name = name
        self.channel = channel
        self.event_type = event_type
        self.subject_template: Optional[str] = None
        self.body_template: str = ""
        self.is_active = True
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.variables: List[str] = []  # Variables disponibles para el template
        self.send_conditions: Dict[str, Any] = {}  # Condiciones para enviar

    def set_templates(self, subject: Optional[str], body: str) -> None:
        """Configurar plantillas de asunto y cuerpo"""
        self.subject_template = subject
        self.body_template = body
        self.updated_at = datetime.now()

    def add_variable(self, variable_name: str) -> None:
        """Agregar variable disponible para el template"""
        if variable_name not in self.variables:
            self.variables.append(variable_name)
            self.updated_at = datetime.now()

    def render(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Renderizar template con contexto dado"""
        # Implementación simplificada de renderizado
        rendered_subject = self.subject_template
        rendered_body = self.body_template
        
        for var_name, var_value in context.items():
            if rendered_subject:
                rendered_subject = rendered_subject.replace(f"{{{var_name}}}", str(var_value))
            rendered_body = rendered_body.replace(f"{{{var_name}}}", str(var_value))
        
        return {
            "subject": rendered_subject,
            "body": rendered_body
        }

    def should_send(self, context: Dict[str, Any]) -> bool:
        """Verificar si se debe enviar la notificación según condiciones"""
        if not self.is_active:
            return False
        
        # Evaluar condiciones de envío
        # Por simplicidad, siempre enviamos si está activo
        return True