from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import json
import hashlib
import hmac
from dataclasses import dataclass

from src.domain.entities.integration import (
    SalesChannelIntegration, WebhookEndpoint, NotificationTemplate,
    ChannelType, IntegrationStatus, AuthConfig, WebhookConfig,
    FieldMapping, IntegrationEvent
)
from src.domain.entities.order import Order
from src.domain.value_objects.customer_id import CustomerId


@dataclass
class SyncResult:
    success: bool
    orders_processed: int
    errors: List[str]
    last_sync_id: Optional[str] = None


@dataclass
class WebhookPayload:
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: Optional[str] = None


class IntegrationService:
    def __init__(self):
        self.integrations: Dict[str, SalesChannelIntegration] = {}
        self.webhook_endpoints: Dict[str, WebhookEndpoint] = {}
        self.notification_templates: Dict[str, NotificationTemplate] = {}
        self.external_api_clients: Dict[ChannelType, Any] = {}

    def create_integration(
        self,
        integration_id: str,
        customer_id: str,
        channel_type: ChannelType,
        channel_name: str,
        auth_config: AuthConfig,
        field_mappings: List[FieldMapping]
    ) -> SalesChannelIntegration:
        """Crear nueva integración con canal de venta"""
        integration = SalesChannelIntegration(
            integration_id=integration_id,
            customer_id=customer_id,
            channel_type=channel_type,
            channel_name=channel_name
        )
        
        integration.configure_auth(auth_config)
        
        for mapping in field_mappings:
            integration.add_field_mapping(mapping)
        
        self.integrations[integration_id] = integration
        
        return integration

    def activate_integration(self, integration_id: str) -> None:
        """Activar integración después de configuración"""
        integration = self.integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integración {integration_id} no encontrada")
        
        # Validar configuración
        if not integration.is_auth_valid():
            raise ValueError("Configuración de autenticación inválida")
        
        integration.activate()
        
        # Inicializar cliente API específico del canal
        self._initialize_api_client(integration)

    def sync_orders(self, integration_id: str, since: datetime = None) -> SyncResult:
        """Sincronizar órdenes desde canal de venta"""
        integration = self.integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integración {integration_id} no encontrada")
        
        if integration.status != IntegrationStatus.ACTIVE:
            raise ValueError("La integración debe estar activa para sincronizar")
        
        try:
            # Obtener órdenes del canal externo
            external_orders = self._fetch_orders_from_channel(integration, since)
            
            # Procesar y transformar órdenes
            processed_orders = []
            errors = []
            
            for external_order in external_orders:
                try:
                    # Verificar si debe sincronizarse
                    if not integration.should_sync_order(external_order):
                        continue
                    
                    # Transformar datos usando mapeos
                    transformed_data = integration.transform_order_data(external_order)
                    
                    # Crear orden en el sistema
                    order = self._create_order_from_integration(
                        integration.customer_id, transformed_data
                    )
                    
                    processed_orders.append(order)
                    
                except Exception as e:
                    errors.append(f"Error procesando orden {external_order.get('id', 'unknown')}: {str(e)}")
            
            # Actualizar estadísticas de integración
            integration.record_sync_success(len(processed_orders))
            
            return SyncResult(
                success=True,
                orders_processed=len(processed_orders),
                errors=errors,
                last_sync_id=external_orders[-1].get('id') if external_orders else None
            )
            
        except Exception as e:
            integration.record_sync_failure(str(e))
            return SyncResult(
                success=False,
                orders_processed=0,
                errors=[str(e)]
            )

    def handle_webhook(
        self,
        endpoint_id: str,
        payload: WebhookPayload,
        headers: Dict[str, str]
    ) -> bool:
        """Manejar webhook entrante"""
        endpoint = self.webhook_endpoints.get(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} no encontrado")
        
        # Validar firma si está configurada
        if endpoint.secret:
            expected_signature = self._calculate_webhook_signature(
                payload.data, endpoint.secret
            )
            
            received_signature = headers.get('X-Signature') or payload.signature
            if not received_signature or not hmac.compare_digest(
                expected_signature, received_signature
            ):
                return False
        
        try:
            # Disparar webhook
            event = endpoint.trigger(payload.data)
            
            # Procesar según tipo de evento
            success = self._process_webhook_event(endpoint, payload)
            
            if success:
                endpoint.record_success(event.event_id)
            else:
                endpoint.record_failure(event.event_id, "Processing failed")
            
            return success
            
        except Exception as e:
            return False

    def create_webhook_endpoint(
        self,
        endpoint_id: str,
        integration_id: str,
        event_type: str,
        url: str,
        secret: Optional[str] = None
    ) -> WebhookEndpoint:
        """Crear endpoint de webhook"""
        endpoint = WebhookEndpoint(
            endpoint_id=endpoint_id,
            integration_id=integration_id,
            event_type=event_type,
            url=url
        )
        
        if secret:
            endpoint.set_secret(secret)
        
        self.webhook_endpoints[endpoint_id] = endpoint
        
        return endpoint

    def send_notification(
        self,
        template_id: str,
        recipient: str,
        context: Dict[str, Any],
        channel: str = "email"
    ) -> bool:
        """Enviar notificación usando template"""
        template = self.notification_templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} no encontrado")
        
        if template.channel != channel:
            raise ValueError(f"Template es para canal {template.channel}, no {channel}")
        
        if not template.should_send(context):
            return False
        
        try:
            # Renderizar contenido
            rendered_content = template.render(context)
            
            # Enviar según canal
            if channel == "email":
                return self._send_email(
                    recipient, rendered_content["subject"], rendered_content["body"]
                )
            elif channel == "sms":
                return self._send_sms(recipient, rendered_content["body"])
            elif channel == "whatsapp":
                return self._send_whatsapp(recipient, rendered_content["body"])
            else:
                return False
                
        except Exception as e:
            return False

    def create_notification_template(
        self,
        template_id: str,
        name: str,
        channel: str,
        event_type: str,
        subject_template: Optional[str],
        body_template: str,
        variables: List[str]
    ) -> NotificationTemplate:
        """Crear template de notificación"""
        template = NotificationTemplate(
            template_id=template_id,
            name=name,
            channel=channel,
            event_type=event_type
        )
        
        template.set_templates(subject_template, body_template)
        
        for variable in variables:
            template.add_variable(variable)
        
        self.notification_templates[template_id] = template
        
        return template

    def update_order_tracking(
        self,
        integration_id: str,
        external_order_id: str,
        tracking_number: str,
        tracking_url: str,
        carrier: str
    ) -> bool:
        """Actualizar tracking en canal externo"""
        integration = self.integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integración {integration_id} no encontrada")
        
        if not integration.auto_update_tracking:
            return False
        
        try:
            api_client = self.external_api_clients.get(integration.channel_type)
            if not api_client:
                return False
            
            # Actualizar tracking según el tipo de canal
            if integration.channel_type == ChannelType.SHOPIFY:
                return self._update_shopify_tracking(
                    api_client, external_order_id, tracking_number, tracking_url, carrier
                )
            elif integration.channel_type == ChannelType.WOOCOMMERCE:
                return self._update_woocommerce_tracking(
                    api_client, external_order_id, tracking_number, tracking_url, carrier
                )
            elif integration.channel_type == ChannelType.MERCADOLIBRE:
                return self._update_mercadolibre_tracking(
                    api_client, external_order_id, tracking_number, carrier
                )
            
            return False
            
        except Exception as e:
            return False

    def get_integration_stats(self, integration_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de integración"""
        integration = self.integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integración {integration_id} no encontrada")
        
        return integration.get_sync_stats()

    def test_integration_connection(self, integration_id: str) -> Dict[str, Any]:
        """Probar conexión con integración"""
        integration = self.integrations.get(integration_id)
        if not integration:
            raise ValueError(f"Integración {integration_id} no encontrada")
        
        try:
            # Realizar prueba de conexión según el tipo de canal
            api_client = self.external_api_clients.get(integration.channel_type)
            if not api_client:
                return {"success": False, "error": "Cliente API no disponible"}
            
            # Intentar obtener información básica
            test_result = self._test_api_connection(integration, api_client)
            
            return {
                "success": test_result["success"],
                "channel_type": integration.channel_type.value,
                "last_test": datetime.now(),
                "response_time_ms": test_result.get("response_time_ms", 0),
                "error": test_result.get("error")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "last_test": datetime.now()
            }

    def _initialize_api_client(self, integration: SalesChannelIntegration) -> None:
        """Inicializar cliente API para el canal"""
        # Implementar inicialización específica por canal
        if integration.channel_type == ChannelType.SHOPIFY:
            self.external_api_clients[integration.channel_type] = self._create_shopify_client(integration)
        elif integration.channel_type == ChannelType.WOOCOMMERCE:
            self.external_api_clients[integration.channel_type] = self._create_woocommerce_client(integration)
        elif integration.channel_type == ChannelType.MERCADOLIBRE:
            self.external_api_clients[integration.channel_type] = self._create_mercadolibre_client(integration)

    def _fetch_orders_from_channel(
        self, 
        integration: SalesChannelIntegration, 
        since: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Obtener órdenes del canal externo"""
        api_client = self.external_api_clients.get(integration.channel_type)
        if not api_client:
            raise ValueError("Cliente API no disponible")
        
        # Implementar obtención de órdenes según el canal
        if integration.channel_type == ChannelType.SHOPIFY:
            return self._fetch_shopify_orders(api_client, since)
        elif integration.channel_type == ChannelType.WOOCOMMERCE:
            return self._fetch_woocommerce_orders(api_client, since)
        elif integration.channel_type == ChannelType.MERCADOLIBRE:
            return self._fetch_mercadolibre_orders(api_client, since)
        
        return []

    def _create_order_from_integration(
        self, 
        customer_id: str, 
        order_data: Dict[str, Any]
    ) -> Order:
        """Crear orden desde datos de integración"""
        # Implementar creación de orden
        # Por simplicidad, retornamos None - en implementación real crearía la orden
        return None

    def _process_webhook_event(
        self, 
        endpoint: WebhookEndpoint, 
        payload: WebhookPayload
    ) -> bool:
        """Procesar evento de webhook"""
        # Implementar procesamiento según tipo de evento
        if payload.event_type == "order_created":
            return self._process_order_created_webhook(endpoint, payload.data)
        elif payload.event_type == "order_updated":
            return self._process_order_updated_webhook(endpoint, payload.data)
        elif payload.event_type == "order_cancelled":
            return self._process_order_cancelled_webhook(endpoint, payload.data)
        
        return False

    def _calculate_webhook_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Calcular firma de webhook"""
        payload_string = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"

    # Métodos de implementación específicos por canal (stubs)
    def _create_shopify_client(self, integration: SalesChannelIntegration):
        """Crear cliente Shopify"""
        # Implementar cliente Shopify
        pass

    def _create_woocommerce_client(self, integration: SalesChannelIntegration):
        """Crear cliente WooCommerce"""
        # Implementar cliente WooCommerce
        pass

    def _create_mercadolibre_client(self, integration: SalesChannelIntegration):
        """Crear cliente MercadoLibre"""
        # Implementar cliente MercadoLibre
        pass

    def _fetch_shopify_orders(self, api_client, since: Optional[datetime]) -> List[Dict[str, Any]]:
        """Obtener órdenes de Shopify"""
        # Implementar fetch de Shopify
        return []

    def _fetch_woocommerce_orders(self, api_client, since: Optional[datetime]) -> List[Dict[str, Any]]:
        """Obtener órdenes de WooCommerce"""
        # Implementar fetch de WooCommerce
        return []

    def _fetch_mercadolibre_orders(self, api_client, since: Optional[datetime]) -> List[Dict[str, Any]]:
        """Obtener órdenes de MercadoLibre"""
        # Implementar fetch de MercadoLibre
        return []

    def _update_shopify_tracking(self, api_client, order_id: str, tracking_number: str, tracking_url: str, carrier: str) -> bool:
        """Actualizar tracking en Shopify"""
        # Implementar actualización en Shopify
        return True

    def _update_woocommerce_tracking(self, api_client, order_id: str, tracking_number: str, tracking_url: str, carrier: str) -> bool:
        """Actualizar tracking en WooCommerce"""
        # Implementar actualización en WooCommerce
        return True

    def _update_mercadolibre_tracking(self, api_client, order_id: str, tracking_number: str, carrier: str) -> bool:
        """Actualizar tracking en MercadoLibre"""
        # Implementar actualización en MercadoLibre
        return True

    def _test_api_connection(self, integration: SalesChannelIntegration, api_client) -> Dict[str, Any]:
        """Probar conexión API"""
        # Implementar prueba de conexión
        return {"success": True, "response_time_ms": 100}

    def _process_order_created_webhook(self, endpoint: WebhookEndpoint, data: Dict[str, Any]) -> bool:
        """Procesar webhook de orden creada"""
        # Implementar procesamiento
        return True

    def _process_order_updated_webhook(self, endpoint: WebhookEndpoint, data: Dict[str, Any]) -> bool:
        """Procesar webhook de orden actualizada"""
        # Implementar procesamiento
        return True

    def _process_order_cancelled_webhook(self, endpoint: WebhookEndpoint, data: Dict[str, Any]) -> bool:
        """Procesar webhook de orden cancelada"""
        # Implementar procesamiento
        return True

    def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Enviar email"""
        # Implementar envío de email
        return True

    def _send_sms(self, recipient: str, message: str) -> bool:
        """Enviar SMS"""
        # Implementar envío de SMS
        return True

    def _send_whatsapp(self, recipient: str, message: str) -> bool:
        """Enviar WhatsApp"""
        # Implementar envío de WhatsApp
        return True