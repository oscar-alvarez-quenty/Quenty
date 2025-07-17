from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from src.domain.events.base_event import DomainEvent


@dataclass
class IntegrationCreated(DomainEvent):
    integration_id: str
    customer_id: str
    channel_type: str
    channel_name: str
    created_by: str


@dataclass
class IntegrationActivated(DomainEvent):
    integration_id: str
    customer_id: str
    channel_type: str
    activated_at: datetime


@dataclass
class IntegrationDeactivated(DomainEvent):
    integration_id: str
    customer_id: str
    deactivation_reason: str
    deactivated_at: datetime


@dataclass
class IntegrationSyncStarted(DomainEvent):
    integration_id: str
    sync_type: str  # "manual", "scheduled", "webhook"
    started_at: datetime
    expected_orders: Optional[int] = None


@dataclass
class IntegrationSyncCompleted(DomainEvent):
    integration_id: str
    sync_duration_seconds: int
    orders_processed: int
    orders_created: int
    orders_updated: int
    errors_count: int
    completed_at: datetime


@dataclass
class IntegrationSyncFailed(DomainEvent):
    integration_id: str
    failure_reason: str
    error_details: str
    failed_at: datetime
    retry_scheduled: bool


@dataclass
class WebhookReceived(DomainEvent):
    integration_id: str
    webhook_id: str
    event_type: str
    payload_size: int
    source_ip: str
    received_at: datetime


@dataclass
class WebhookProcessed(DomainEvent):
    integration_id: str
    webhook_id: str
    processing_result: str  # "success", "failed", "ignored"
    processing_time_ms: int
    actions_taken: list
    processed_at: datetime


@dataclass
class WebhookFailed(DomainEvent):
    integration_id: str
    webhook_id: str
    failure_reason: str
    retry_count: int
    max_retries_reached: bool
    failed_at: datetime


@dataclass
class OrderImported(DomainEvent):
    integration_id: str
    external_order_id: str
    internal_order_id: str
    customer_id: str
    order_amount: float
    imported_at: datetime


@dataclass
class OrderUpdatePushed(DomainEvent):
    integration_id: str
    external_order_id: str
    internal_order_id: str
    update_type: str  # "status", "tracking", "cancellation"
    update_data: Dict[str, Any]
    pushed_at: datetime


@dataclass
class TrackingUpdateSent(DomainEvent):
    integration_id: str
    external_order_id: str
    tracking_number: str
    tracking_status: str
    carrier_name: str
    sent_at: datetime


@dataclass
class IntegrationAuthenticationRefreshed(DomainEvent):
    integration_id: str
    auth_type: str
    refresh_reason: str
    expires_at: Optional[datetime]
    refreshed_at: datetime


@dataclass
class IntegrationAuthenticationFailed(DomainEvent):
    integration_id: str
    auth_type: str
    failure_reason: str
    retry_scheduled: bool
    failed_at: datetime


@dataclass
class NotificationSent(DomainEvent):
    template_id: str
    recipient: str
    channel: str  # "email", "sms", "whatsapp", "push"
    notification_type: str
    sent_at: datetime
    delivery_status: str  # "sent", "delivered", "failed"


@dataclass
class NotificationFailed(DomainEvent):
    template_id: str
    recipient: str
    channel: str
    failure_reason: str
    retry_count: int
    failed_at: datetime


@dataclass
class NotificationTemplateCreated(DomainEvent):
    template_id: str
    name: str
    channel: str
    event_type: str
    created_by: str
    created_at: datetime


@dataclass
class NotificationTemplateUpdated(DomainEvent):
    template_id: str
    updated_fields: list
    updated_by: str
    updated_at: datetime


@dataclass
class IntegrationQuotaExceeded(DomainEvent):
    integration_id: str
    quota_type: str  # "api_calls", "orders", "storage"
    current_usage: int
    quota_limit: int
    period: str  # "daily", "monthly"
    exceeded_at: datetime


@dataclass
class IntegrationPerformanceAlert(DomainEvent):
    integration_id: str
    metric_name: str  # "response_time", "error_rate", "success_rate"
    current_value: float
    threshold_value: float
    alert_severity: str  # "warning", "critical"
    detected_at: datetime


@dataclass
class FieldMappingUpdated(DomainEvent):
    integration_id: str
    mapping_changes: list
    updated_by: str
    updated_at: datetime


@dataclass
class IntegrationHealthCheckFailed(DomainEvent):
    integration_id: str
    health_check_type: str
    failure_details: str
    consecutive_failures: int
    check_time: datetime


@dataclass
class ExternalAPIRateLimitReached(DomainEvent):
    integration_id: str
    api_endpoint: str
    rate_limit: int
    reset_time: datetime
    affected_operations: list