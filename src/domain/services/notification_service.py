from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from src.domain.value_objects.email import Email
from src.domain.value_objects.phone import Phone

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"

@dataclass
class NotificationTemplate:
    id: str
    name: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    is_active: bool = True
    variables: List[str] = None

@dataclass
class NotificationRequest:
    recipient_id: str
    recipient_email: Optional[Email] = None
    recipient_phone: Optional[Phone] = None
    channel: NotificationChannel
    template_id: str
    variables: Dict[str, Any] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    scheduled_at: Optional[str] = None  # ISO datetime string

@dataclass
class NotificationResult:
    success: bool
    notification_id: str
    channel: NotificationChannel
    status: NotificationStatus
    message: str = ""
    external_id: str = ""

class NotificationProvider(ABC):
    """Interfaz para proveedores de notificaciones"""
    
    @abstractmethod
    async def send_email(self, to: Email, subject: str, body: str, 
                        html_body: str = None) -> NotificationResult:
        pass
    
    @abstractmethod
    async def send_sms(self, to: Phone, message: str) -> NotificationResult:
        pass
    
    @abstractmethod
    async def send_whatsapp(self, to: Phone, message: str, 
                           template_name: str = None) -> NotificationResult:
        pass

class NotificationService:
    """Servicio de dominio para manejo de notificaciones"""
    
    def __init__(self):
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self._initialize_default_templates()
    
    def register_provider(self, channel: NotificationChannel, 
                         provider: NotificationProvider) -> None:
        """Registra un proveedor de notificaciones"""
        self.providers[channel] = provider
    
    def register_template(self, template: NotificationTemplate) -> None:
        """Registra una plantilla de notificación"""
        self.templates[template.id] = template
    
    def _initialize_default_templates(self) -> None:
        """Inicializa plantillas por defecto"""
        
        # Template para bienvenida de cliente
        self.register_template(NotificationTemplate(
            id="customer_welcome",
            name="Customer Welcome",
            channel=NotificationChannel.EMAIL,
            subject_template="¡Bienvenido a Quenty, {customer_name}!",
            body_template="""
            Hola {customer_name},
            
            ¡Bienvenido a Quenty! Tu cuenta ha sido creada exitosamente.
            
            Email: {customer_email}
            Tipo de cliente: {customer_type}
            
            Ahora puedes comenzar a crear tus envíos.
            
            Saludos,
            Equipo Quenty
            """,
            variables=["customer_name", "customer_email", "customer_type"]
        ))
        
        # Template para orden creada
        self.register_template(NotificationTemplate(
            id="order_created",
            name="Order Created",
            channel=NotificationChannel.EMAIL,
            subject_template="Orden #{order_id} creada exitosamente",
            body_template="""
            Hola {customer_name},
            
            Tu orden #{order_id} ha sido creada exitosamente.
            
            Destino: {destination_city}
            Valor declarado: ${declared_value}
            Estado: {order_status}
            
            Te notificaremos cuando tengamos la cotización lista.
            
            Saludos,
            Equipo Quenty
            """,
            variables=["customer_name", "order_id", "destination_city", "declared_value", "order_status"]
        ))
        
        # Template para guía generada
        self.register_template(NotificationTemplate(
            id="guide_generated",
            name="Guide Generated",
            channel=NotificationChannel.EMAIL,
            subject_template="Guía #{guide_id} generada - Orden #{order_id}",
            body_template="""
            Hola {customer_name},
            
            La guía para tu orden #{order_id} ha sido generada.
            
            Número de guía: {guide_id}
            Operador logístico: {logistics_operator}
            
            Puedes hacer seguimiento en: {tracking_url}
            
            Saludos,
            Equipo Quenty
            """,
            variables=["customer_name", "order_id", "guide_id", "logistics_operator", "tracking_url"]
        ))
        
        # Template para paquete entregado
        self.register_template(NotificationTemplate(
            id="package_delivered",
            name="Package Delivered",
            channel=NotificationChannel.SMS,
            subject_template="",  # SMS no usa subject
            body_template="¡Tu paquete {guide_id} ha sido entregado exitosamente a {recipient_name} en {delivery_location}! - Quenty",
            variables=["guide_id", "recipient_name", "delivery_location"]
        ))
        
        # Template para KYC validado
        self.register_template(NotificationTemplate(
            id="kyc_validated",
            name="KYC Validated",
            channel=NotificationChannel.EMAIL,
            subject_template="Validación KYC completada - ¡Envíos internacionales habilitados!",
            body_template="""
            Hola {customer_name},
            
            Tu validación KYC ha sido completada exitosamente.
            
            Ahora puedes realizar envíos internacionales y acceder a más beneficios.
            
            Saludos,
            Equipo Quenty
            """,
            variables=["customer_name"]
        ))
    
    async def send_notification(self, request: NotificationRequest) -> NotificationResult:
        """Envía una notificación"""
        
        # Validar que existe la plantilla
        if request.template_id not in self.templates:
            return NotificationResult(
                success=False,
                notification_id="",
                channel=request.channel,
                status=NotificationStatus.FAILED,
                message=f"Template {request.template_id} not found"
            )
        
        template = self.templates[request.template_id]
        
        # Validar que existe el proveedor
        if request.channel not in self.providers:
            return NotificationResult(
                success=False,
                notification_id="",
                channel=request.channel,
                status=NotificationStatus.FAILED,
                message=f"Provider for channel {request.channel.value} not registered"
            )
        
        provider = self.providers[request.channel]
        
        # Renderizar la plantilla
        try:
            rendered_content = self._render_template(template, request.variables or {})
        except Exception as e:
            return NotificationResult(
                success=False,
                notification_id="",
                channel=request.channel,
                status=NotificationStatus.FAILED,
                message=f"Template rendering failed: {str(e)}"
            )
        
        # Enviar según el canal
        try:
            if request.channel == NotificationChannel.EMAIL:
                return await provider.send_email(
                    request.recipient_email,
                    rendered_content["subject"],
                    rendered_content["body"]
                )
            elif request.channel == NotificationChannel.SMS:
                return await provider.send_sms(
                    request.recipient_phone,
                    rendered_content["body"]
                )
            elif request.channel == NotificationChannel.WHATSAPP:
                return await provider.send_whatsapp(
                    request.recipient_phone,
                    rendered_content["body"]
                )
            else:
                return NotificationResult(
                    success=False,
                    notification_id="",
                    channel=request.channel,
                    status=NotificationStatus.FAILED,
                    message=f"Channel {request.channel.value} not implemented"
                )
        
        except Exception as e:
            return NotificationResult(
                success=False,
                notification_id="",
                channel=request.channel,
                status=NotificationStatus.FAILED,
                message=f"Send failed: {str(e)}"
            )
    
    async def send_customer_welcome(self, customer_name: str, customer_email: Email, 
                                  customer_type: str) -> NotificationResult:
        """Envía notificación de bienvenida a cliente"""
        
        request = NotificationRequest(
            recipient_id=customer_email.value,
            recipient_email=customer_email,
            channel=NotificationChannel.EMAIL,
            template_id="customer_welcome",
            variables={
                "customer_name": customer_name,
                "customer_email": customer_email.value,
                "customer_type": customer_type
            }
        )
        
        return await self.send_notification(request)
    
    async def send_order_confirmation(self, customer_name: str, customer_email: Email,
                                    order_id: str, destination_city: str, 
                                    declared_value: str) -> NotificationResult:
        """Envía confirmación de orden creada"""
        
        request = NotificationRequest(
            recipient_id=customer_email.value,
            recipient_email=customer_email,
            channel=NotificationChannel.EMAIL,
            template_id="order_created",
            variables={
                "customer_name": customer_name,
                "order_id": order_id,
                "destination_city": destination_city,
                "declared_value": declared_value,
                "order_status": "Pendiente"
            }
        )
        
        return await self.send_notification(request)
    
    async def send_guide_generated(self, customer_name: str, customer_email: Email,
                                 order_id: str, guide_id: str, 
                                 logistics_operator: str) -> NotificationResult:
        """Envía notificación de guía generada"""
        
        tracking_url = f"https://track.quenty.com/{guide_id}"
        
        request = NotificationRequest(
            recipient_id=customer_email.value,
            recipient_email=customer_email,
            channel=NotificationChannel.EMAIL,
            template_id="guide_generated",
            variables={
                "customer_name": customer_name,
                "order_id": order_id,
                "guide_id": guide_id,
                "logistics_operator": logistics_operator,
                "tracking_url": tracking_url
            }
        )
        
        return await self.send_notification(request)
    
    async def send_delivery_notification(self, recipient_phone: Phone, guide_id: str,
                                       recipient_name: str, delivery_location: str) -> NotificationResult:
        """Envía notificación de entrega por SMS"""
        
        request = NotificationRequest(
            recipient_id=recipient_phone.get_full_number(),
            recipient_phone=recipient_phone,
            channel=NotificationChannel.SMS,
            template_id="package_delivered",
            variables={
                "guide_id": guide_id,
                "recipient_name": recipient_name,
                "delivery_location": delivery_location
            }
        )
        
        return await self.send_notification(request)
    
    def _render_template(self, template: NotificationTemplate, 
                        variables: Dict[str, Any]) -> Dict[str, str]:
        """Renderiza una plantilla con las variables proporcionadas"""
        
        try:
            subject = template.subject_template.format(**variables)
            body = template.body_template.format(**variables)
            
            return {
                "subject": subject,
                "body": body
            }
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
        except Exception as e:
            raise ValueError(f"Template rendering error: {e}")
    
    def get_available_templates(self) -> List[NotificationTemplate]:
        """Obtiene todas las plantillas disponibles"""
        return list(self.templates.values())
    
    def get_templates_by_channel(self, channel: NotificationChannel) -> List[NotificationTemplate]:
        """Obtiene plantillas por canal"""
        return [t for t in self.templates.values() if t.channel == channel]