from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.domain.events.base_event import DomainEvent


@dataclass
class ReturnRequested(DomainEvent):
    return_id: str
    customer_id: str
    original_guide_id: str
    return_reason: str
    items_count: int
    expected_value: Dict[str, Any]  # amount and currency
    requested_at: datetime


@dataclass
class ReturnApproved(DomainEvent):
    return_id: str
    customer_id: str
    approved_by: str
    return_deadline: datetime
    pickup_scheduled: bool
    pickup_date: Optional[datetime]
    approved_at: datetime


@dataclass
class ReturnRejected(DomainEvent):
    return_id: str
    customer_id: str
    rejection_reason: str
    rejected_by: str
    rejected_at: datetime


@dataclass
class ReturnItemAdded(DomainEvent):
    return_id: str
    item_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: Dict[str, Any]
    return_reason: str
    added_at: datetime


@dataclass
class ReturnPickupScheduled(DomainEvent):
    return_id: str
    customer_id: str
    pickup_date: datetime
    pickup_address: str
    assigned_operator: str
    scheduled_at: datetime


@dataclass
class ReturnShipmentCreated(DomainEvent):
    return_id: str
    return_guide_id: str
    carrier: str
    tracking_number: str
    estimated_delivery: datetime
    created_at: datetime


@dataclass
class ReturnInTransit(DomainEvent):
    return_id: str
    return_guide_id: str
    carrier: str
    origin: str
    destination: str
    estimated_arrival: datetime
    transit_started_at: datetime


@dataclass
class ReturnReceived(DomainEvent):
    return_id: str
    received_at_center: str
    received_by: str
    packages_count: int
    initial_condition: str
    received_at: datetime


@dataclass
class ReturnInspectionStarted(DomainEvent):
    return_id: str
    inspection_id: str
    inspector_id: str
    center_id: str
    items_to_inspect: int
    started_at: datetime


@dataclass
class ReturnInspectionCompleted(DomainEvent):
    return_id: str
    inspection_id: str
    inspector_id: str
    overall_result: str  # "approved", "rejected", "partial_approval"
    approved_items: int
    rejected_items: int
    refund_amount: Dict[str, Any]
    completed_at: datetime


@dataclass
class ReturnItemInspected(DomainEvent):
    return_id: str
    inspection_id: str
    item_id: str
    product_id: str
    inspection_result: str
    condition_score: float  # 0.0 to 1.0
    disposition_action: str
    notes: str
    inspected_at: datetime


@dataclass
class ReturnRefundProcessed(DomainEvent):
    return_id: str
    customer_id: str
    refund_amount: Dict[str, Any]
    refund_method: str
    transaction_reference: str
    processed_by: str
    processed_at: datetime


@dataclass
class ReturnRefundFailed(DomainEvent):
    return_id: str
    customer_id: str
    attempted_amount: Dict[str, Any]
    refund_method: str
    failure_reason: str
    retry_scheduled: bool
    failed_at: datetime


@dataclass
class ReturnExchangeProcessed(DomainEvent):
    return_id: str
    customer_id: str
    original_items: List[str]
    exchange_items: List[str]
    price_difference: Dict[str, Any]
    processed_by: str
    processed_at: datetime


@dataclass
class ReturnCancelled(DomainEvent):
    return_id: str
    customer_id: str
    cancellation_reason: str
    cancelled_by: str
    refund_applicable: bool
    cancelled_at: datetime


@dataclass
class ReturnDeadlineExpired(DomainEvent):
    return_id: str
    customer_id: str
    original_deadline: datetime
    auto_cancelled: bool
    expired_at: datetime


@dataclass
class InventoryRestocked(DomainEvent):
    center_id: str
    return_id: str
    product_id: str
    quantity_restocked: int
    condition: str  # "new", "refurbished", "damaged"
    restocked_by: str
    restocked_at: datetime


@dataclass
class InventoryDisposed(DomainEvent):
    center_id: str
    return_id: str
    product_id: str
    quantity_disposed: int
    disposal_method: str  # "recycle", "donate", "destroy"
    disposal_reason: str
    disposed_by: str
    disposed_at: datetime


@dataclass
class ReturnPolicyCreated(DomainEvent):
    policy_id: str
    policy_name: str
    return_window_days: int
    eligible_reasons: List[str]
    created_by: str
    created_at: datetime


@dataclass
class ReturnPolicyUpdated(DomainEvent):
    policy_id: str
    updated_fields: List[str]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    updated_by: str
    updated_at: datetime


@dataclass
class ReverseLogisticsCenterCreated(DomainEvent):
    center_id: str
    center_name: str
    address: str
    capacity: int
    created_by: str
    created_at: datetime


@dataclass
class CenterCapacityExceeded(DomainEvent):
    center_id: str
    current_inventory: int
    maximum_capacity: int
    overflow_amount: int
    alert_severity: str
    detected_at: datetime


@dataclass
class ReturnProcessingDelayed(DomainEvent):
    return_id: str
    center_id: str
    expected_processing_time: int  # hours
    actual_time_elapsed: int  # hours
    delay_reason: str
    estimated_completion: datetime
    detected_at: datetime


@dataclass
class QualityControlAlert(DomainEvent):
    alert_id: str
    center_id: str
    product_id: str
    issue_type: str  # "high_return_rate", "quality_degradation", "fraud_suspicion"
    affected_returns: List[str]
    alert_severity: str
    detected_at: datetime


@dataclass
class ReturnFraudDetected(DomainEvent):
    return_id: str
    customer_id: str
    fraud_indicators: List[str]
    risk_score: float
    auto_blocked: bool
    investigation_required: bool
    detected_at: datetime


@dataclass
class ReturnLabelGenerated(DomainEvent):
    return_id: str
    customer_id: str
    label_type: str  # "prepaid", "customer_pay"
    carrier: str
    tracking_number: str
    expiry_date: datetime
    generated_at: datetime


@dataclass
class ReturnCustomerNotified(DomainEvent):
    return_id: str
    customer_id: str
    notification_type: str  # "approved", "rejected", "received", "refunded"
    channel: str  # "email", "sms", "whatsapp", "push"
    message_content: str
    sent_at: datetime


@dataclass
class ReturnAnalyticsCalculated(DomainEvent):
    calculation_id: str
    period_start: datetime
    period_end: datetime
    total_returns: int
    total_refund_amount: Dict[str, Any]
    return_rate_percentage: float
    top_return_reasons: List[Dict[str, Any]]
    calculated_at: datetime


@dataclass
class ReturnCostAnalyzed(DomainEvent):
    analysis_id: str
    return_id: str
    processing_cost: Dict[str, Any]
    shipping_cost: Dict[str, Any]
    inspection_cost: Dict[str, Any]
    total_cost: Dict[str, Any]
    cost_vs_refund_ratio: float
    analyzed_at: datetime


@dataclass
class ReturnTrendAlert(DomainEvent):
    alert_id: str
    trend_type: str  # "spike", "pattern", "anomaly"
    product_category: str
    return_reason: str
    trend_percentage: float
    time_period: str
    alert_threshold: float
    detected_at: datetime


@dataclass
class ReturnRestockingCompleted(DomainEvent):
    center_id: str
    batch_id: str
    products_restocked: int
    total_value: Dict[str, Any]
    condition_breakdown: Dict[str, int]  # condition -> count
    completed_by: str
    completed_at: datetime


@dataclass
class ReturnDispositionRecommended(DomainEvent):
    recommendation_id: str
    product_id: str
    current_condition: str
    recommended_action: str  # "restock", "refurbish", "dispose"
    confidence_score: float
    cost_analysis: Dict[str, Any]
    recommended_at: datetime


@dataclass
class ReturnMetricsThresholdBreached(DomainEvent):
    metric_name: str
    current_value: float
    threshold_value: float
    breach_type: str  # "above", "below"
    severity: str
    affected_period: str
    detected_at: datetime