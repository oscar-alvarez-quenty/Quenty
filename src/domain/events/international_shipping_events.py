from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.domain.events.base_event import DomainEvent


@dataclass
class KYCValidationStarted(DomainEvent):
    kyc_id: str
    customer_id: str
    provider: str
    validation_type: str


@dataclass
class KYCDocumentSubmitted(DomainEvent):
    kyc_id: str
    customer_id: str
    document_type: str
    file_url: str
    submitted_at: datetime


@dataclass
class KYCValidationApproved(DomainEvent):
    kyc_id: str
    customer_id: str
    approved_by: str
    validation_score: float
    risk_level: str
    expiry_date: datetime
    approved_at: datetime


@dataclass
class KYCValidationRejected(DomainEvent):
    kyc_id: str
    customer_id: str
    rejection_reasons: List[str]
    rejected_at: datetime


@dataclass
class KYCValidationExpired(DomainEvent):
    kyc_id: str
    customer_id: str
    expired_at: datetime
    renewal_required: bool


@dataclass
class InternationalShipmentCreated(DomainEvent):
    shipment_id: str
    guide_id: str
    customer_id: str
    destination_country: str
    declared_value: Dict[str, Any]  # amount and currency
    created_at: datetime


@dataclass
class InternationalDocumentUploaded(DomainEvent):
    document_id: str
    shipment_id: str
    guide_id: str
    document_type: str
    file_url: str
    uploaded_at: datetime


@dataclass
class InternationalDocumentTranslated(DomainEvent):
    document_id: str
    shipment_id: str
    original_language: str
    target_language: str
    translated_file_url: str
    translated_at: datetime


@dataclass
class InternationalDocumentValidated(DomainEvent):
    document_id: str
    shipment_id: str
    document_type: str
    is_valid: bool
    validated_by: str
    validation_notes: Optional[str]
    validated_at: datetime


@dataclass
class CustomsDeclarationCreated(DomainEvent):
    declaration_id: str
    shipment_id: str
    guide_id: str
    declared_value: Dict[str, Any]
    product_description: str
    product_category: str
    hs_code: Optional[str]
    created_at: datetime


@dataclass
class CountryRestrictionsValidated(DomainEvent):
    shipment_id: str
    destination_country: str
    compliance_status: str  # "compliant", "non_compliant"
    restrictions_checked: int
    compliance_issues: List[str]
    validated_at: datetime


@dataclass
class CustomsClearanceStarted(DomainEvent):
    shipment_id: str
    guide_id: str
    customs_tracking_number: str
    estimated_clearance_date: datetime
    started_at: datetime


@dataclass
class CustomsClearanceCompleted(DomainEvent):
    shipment_id: str
    guide_id: str
    customs_tracking_number: str
    customs_fees: Dict[str, Any]  # amount and currency
    actual_clearance_date: datetime
    clearance_duration_hours: int


@dataclass
class CustomsDetention(DomainEvent):
    shipment_id: str
    guide_id: str
    customs_tracking_number: str
    detention_reason: str
    detention_date: datetime
    resolution_required: bool


@dataclass
class InternationalShipmentReadyForShipping(DomainEvent):
    shipment_id: str
    guide_id: str
    kyc_status: str
    documents_complete: bool
    customs_ready: bool
    compliance_verified: bool
    ready_at: datetime


@dataclass
class InternationalCostsCalculated(DomainEvent):
    shipment_id: str
    guide_id: str
    customs_fees: Dict[str, Any]
    insurance_amount: Dict[str, Any]
    total_international_costs: Dict[str, Any]
    calculated_at: datetime


@dataclass
class CountryRestrictionViolation(DomainEvent):
    shipment_id: str
    destination_country: str
    violation_type: str  # "value_exceeded", "weight_exceeded", "prohibited", "missing_documents"
    violation_details: str
    detected_at: datetime


@dataclass
class InternationalDocumentExpired(DomainEvent):
    document_id: str
    shipment_id: str
    document_type: str
    expired_at: datetime
    renewal_required: bool


@dataclass
class InternationalShippingQuoteRequested(DomainEvent):
    shipment_id: str
    destination_country: str
    declared_value: Dict[str, Any]
    weight_kg: float
    dimensions_cm: Dict[str, float]
    requested_at: datetime


@dataclass
class InternationalCarrierSelected(DomainEvent):
    shipment_id: str
    carrier_name: str
    service_type: str
    estimated_delivery_days: int
    shipping_cost: Dict[str, Any]
    selected_at: datetime


@dataclass
class HSCodeAssigned(DomainEvent):
    declaration_id: str
    shipment_id: str
    product_description: str
    assigned_hs_code: str
    assigned_by: str
    confidence_score: Optional[float]
    assigned_at: datetime


@dataclass
class InternationalInsuranceApplied(DomainEvent):
    shipment_id: str
    insurance_type: str
    coverage_amount: Dict[str, Any]
    premium_amount: Dict[str, Any]
    policy_number: str
    applied_at: datetime


@dataclass
class InternationalTrackingUpdateReceived(DomainEvent):
    shipment_id: str
    tracking_number: str
    status: str
    location: str
    carrier: str
    update_timestamp: datetime
    received_at: datetime


@dataclass
class InternationalDeliveryAttempted(DomainEvent):
    shipment_id: str
    tracking_number: str
    attempt_number: int
    delivery_status: str  # "delivered", "failed", "partial"
    failure_reason: Optional[str]
    attempted_at: datetime


@dataclass
class InternationalShipmentDelivered(DomainEvent):
    shipment_id: str
    guide_id: str
    tracking_number: str
    delivered_to: str
    delivery_signature: Optional[str]
    delivery_photo_url: Optional[str]
    delivered_at: datetime


@dataclass
class InternationalShipmentReturned(DomainEvent):
    shipment_id: str
    guide_id: str
    return_reason: str
    return_tracking_number: Optional[str]
    returned_at: datetime
    refund_applicable: bool


@dataclass
class DutyTaxCalculated(DomainEvent):
    shipment_id: str
    destination_country: str
    duty_amount: Dict[str, Any]
    tax_amount: Dict[str, Any]
    total_amount: Dict[str, Any]
    calculation_method: str
    calculated_at: datetime


@dataclass
class InternationalComplianceAudit(DomainEvent):
    audit_id: str
    shipment_id: str
    audit_type: str  # "routine", "random", "complaint"
    audit_status: str  # "passed", "failed", "pending"
    findings: List[str]
    audited_by: str
    audited_at: datetime