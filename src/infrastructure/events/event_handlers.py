from src.domain.events.base_event import EventHandler, DomainEvent
from src.domain.events.customer_events import CustomerCreated, CustomerKYCValidated, WalletCredited
from src.domain.events.order_events import OrderCreated, GuideGenerated, PackageDelivered
from src.domain.events.payment_events import PaymentProcessed, CommissionCalculated
from src.infrastructure.logging.logger import logger, log_customer_created, log_order_created, log_payment_processed
from src.infrastructure.logging.log_messages import LogCodes

class CustomerEventHandler(EventHandler):
    """Manejador de eventos de cliente"""
    
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, CustomerCreated):
            await self._handle_customer_created(event)
        elif isinstance(event, CustomerKYCValidated):
            await self._handle_kyc_validated(event)
        elif isinstance(event, WalletCredited):
            await self._handle_wallet_credited(event)
    
    def can_handle(self, event_type: str) -> bool:
        return event_type.startswith("customer.") or event_type.startswith("wallet.")
    
    async def _handle_customer_created(self, event: CustomerCreated) -> None:
        """Maneja la creación de un cliente"""
        # Log estructurado
        log_customer_created(event.customer_id, event.email)
        
        # Aquí podrían ir otras acciones como:
        # - Enviar email de bienvenida
        # - Crear wallet automáticamente
        # - Notificar a sistemas externos
        # - Registrar métricas
        
        logger.info("Customer creation event processed successfully",
                   customer_id=event.customer_id,
                   customer_type=event.customer_type.value)
    
    async def _handle_kyc_validated(self, event: CustomerKYCValidated) -> None:
        """Maneja la validación KYC"""
        logger.log_with_code(LogCodes.CUSTOMER_KYC_VALIDATED, 
                           customer_id=event.customer_id)
        
        # Acciones post-KYC:
        # - Habilitar servicios internacionales
        # - Aumentar límites de crédito
        # - Notificar al cliente
    
    async def _handle_wallet_credited(self, event: WalletCredited) -> None:
        """Maneja el crédito al wallet"""
        logger.log_with_code(LogCodes.WALLET_CREDITED,
                           wallet_id=event.wallet_id,
                           amount=event.amount,
                           balance=event.amount)  # Simplificado

class OrderEventHandler(EventHandler):
    """Manejador de eventos de órdenes"""
    
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, OrderCreated):
            await self._handle_order_created(event)
        elif isinstance(event, GuideGenerated):
            await self._handle_guide_generated(event)
        elif isinstance(event, PackageDelivered):
            await self._handle_package_delivered(event)
    
    def can_handle(self, event_type: str) -> bool:
        return (event_type.startswith("order.") or 
                event_type.startswith("guide.") or 
                event_type.startswith("package."))
    
    async def _handle_order_created(self, event: OrderCreated) -> None:
        """Maneja la creación de una orden"""
        log_order_created(event.order_id, event.customer_id, event.destination_city)
        
        # Acciones automáticas:
        # - Validar inventario si aplica
        # - Notificar al área de operaciones
        # - Iniciar proceso de cotización automática
        # - Registrar métricas de demanda
    
    async def _handle_guide_generated(self, event: GuideGenerated) -> None:
        """Maneja la generación de guía"""
        logger.log_with_code(LogCodes.GUIDE_GENERATED,
                           guide_id=event.guide_id,
                           order_id=event.order_id,
                           operator=event.logistics_operator)
        
        # Acciones post-generación:
        # - Enviar guía por email
        # - Notificar al operador logístico
        # - Programar recolección
        # - Actualizar tracking
    
    async def _handle_package_delivered(self, event: PackageDelivered) -> None:
        """Maneja la entrega del paquete"""
        logger.log_with_code(LogCodes.GUIDE_DELIVERED,
                           guide_id=event.guide_id,
                           recipient=event.recipient_name,
                           delivery_date=event.delivery_timestamp)
        
        # Acciones post-entrega:
        # - Calcular comisiones
        # - Enviar notificación de entrega
        # - Procesar pago contra entrega si aplica
        # - Generar encuesta de satisfacción

class PaymentEventHandler(EventHandler):
    """Manejador de eventos de pagos"""
    
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, PaymentProcessed):
            await self._handle_payment_processed(event)
        elif isinstance(event, CommissionCalculated):
            await self._handle_commission_calculated(event)
    
    def can_handle(self, event_type: str) -> bool:
        return (event_type.startswith("payment.") or 
                event_type.startswith("commission.") or
                event_type.startswith("cod."))
    
    async def _handle_payment_processed(self, event: PaymentProcessed) -> None:
        """Maneja el procesamiento de pago"""
        log_payment_processed(event.transaction_reference, event.amount, event.payment_method)
        
        # Acciones post-pago:
        # - Actualizar estado de orden
        # - Enviar comprobante
        # - Activar servicios pagados
        # - Registrar en contabilidad
    
    async def _handle_commission_calculated(self, event: CommissionCalculated) -> None:
        """Maneja el cálculo de comisión"""
        logger.log_with_code(LogCodes.COMMISSION_CALCULATED,
                           commission_id=event.commission_id,
                           recipient_id=event.recipient_id,
                           amount=event.commission_amount)
        
        # Acciones post-cálculo:
        # - Notificar al beneficiario
        # - Programar liquidación
        # - Actualizar reportes

class NotificationHandler(EventHandler):
    """Manejador genérico para notificaciones"""
    
    async def handle(self, event: DomainEvent) -> None:
        """Maneja todas las notificaciones"""
        await self._send_notification(event)
    
    def can_handle(self, event_type: str) -> bool:
        # Este handler puede manejar cualquier evento para notificaciones
        return True
    
    async def _send_notification(self, event: DomainEvent) -> None:
        """Envía notificaciones basadas en el evento"""
        event_type = event.get_event_type()
        event_data = event.to_dict()
        
        # Aquí se integraría con servicios de notificación:
        # - Email (SendGrid, AWS SES)
        # - SMS (Twilio)
        # - WhatsApp
        # - Push notifications
        # - Webhooks a sistemas externos
        
        logger.info(f"Notification triggered for event: {event_type}",
                   event_id=str(event.event_id),
                   notification_channels=["email", "sms"])

class MetricsHandler(EventHandler):
    """Manejador para métricas y analytics"""
    
    async def handle(self, event: DomainEvent) -> None:
        """Registra métricas basadas en eventos"""
        await self._record_metrics(event)
    
    def can_handle(self, event_type: str) -> bool:
        return True  # Registra métricas para todos los eventos
    
    async def _record_metrics(self, event: DomainEvent) -> None:
        """Registra métricas del evento"""
        event_type = event.get_event_type()
        
        # Aquí se integraría con sistemas de métricas:
        # - Incrementar contadores
        # - Registrar latencias
        # - Actualizar dashboards
        # - Enviar a sistemas como Prometheus, DataDog, etc.
        
        logger.debug(f"Metrics recorded for event: {event_type}",
                    event_type=event_type,
                    aggregate_type=event.aggregate_type)

# Función para registrar todos los handlers
async def register_event_handlers(event_bus):
    """Registra todos los handlers de eventos"""
    
    # Handlers específicos de dominio
    customer_handler = CustomerEventHandler()
    order_handler = OrderEventHandler()
    payment_handler = PaymentEventHandler()
    
    # Handlers transversales
    notification_handler = NotificationHandler()
    metrics_handler = MetricsHandler()
    
    # Registrar handlers específicos
    await event_bus.subscribe("customer.created", customer_handler)
    await event_bus.subscribe("customer.kyc_validated", customer_handler)
    await event_bus.subscribe("wallet.credited", customer_handler)
    await event_bus.subscribe("wallet.debited", customer_handler)
    
    await event_bus.subscribe("order.created", order_handler)
    await event_bus.subscribe("order.confirmed", order_handler)
    await event_bus.subscribe("guide.generated", order_handler)
    await event_bus.subscribe("package.delivered", order_handler)
    
    await event_bus.subscribe("payment.processed", payment_handler)
    await event_bus.subscribe("commission.calculated", payment_handler)
    
    # Registrar handlers transversales para todos los eventos
    event_types = [
        "customer.created", "customer.updated", "customer.kyc_validated",
        "order.created", "order.quoted", "order.confirmed", "order.cancelled",
        "guide.generated", "package.picked_up", "package.delivered",
        "payment.processed", "payment.failed", "commission.calculated"
    ]
    
    for event_type in event_types:
        await event_bus.subscribe(event_type, notification_handler)
        await event_bus.subscribe(event_type, metrics_handler)
    
    logger.info("All event handlers registered successfully")