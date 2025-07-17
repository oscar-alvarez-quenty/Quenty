from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.domain.events.base_event import DomainEvent


@dataclass
class MicrocreditApplicationSubmitted(DomainEvent):
    application_id: str
    customer_id: str
    requested_amount: Dict[str, Any]  # amount and currency
    purpose: str
    submitted_at: datetime


@dataclass
class CreditScoringStarted(DomainEvent):
    application_id: str
    customer_id: str
    scoring_model_version: str
    data_sources: List[str]
    started_at: datetime


@dataclass
class CreditScoringCompleted(DomainEvent):
    application_id: str
    customer_id: str
    credit_score: int
    risk_level: str
    scoring_factors: Dict[str, float]
    recommendation: str  # "approve", "reject", "manual_review"
    completed_at: datetime


@dataclass
class MicrocreditApproved(DomainEvent):
    microcredit_id: str
    application_id: str
    customer_id: str
    approved_amount: Dict[str, Any]
    interest_rate: float
    term_months: int
    approved_by: str
    approved_at: datetime


@dataclass
class MicrocreditRejected(DomainEvent):
    application_id: str
    customer_id: str
    rejection_reasons: List[str]
    rejection_code: str
    rejected_by: str
    rejected_at: datetime


@dataclass
class MicrocreditDisbursed(DomainEvent):
    microcredit_id: str
    customer_id: str
    disbursed_amount: Dict[str, Any]
    disbursement_method: str  # "wallet", "bank_transfer", "cash"
    reference_number: str
    disbursed_at: datetime


@dataclass
class PaymentScheduleGenerated(DomainEvent):
    microcredit_id: str
    customer_id: str
    total_payments: int
    payment_frequency: str  # "weekly", "monthly"
    first_payment_date: datetime
    total_amount: Dict[str, Any]
    generated_at: datetime


@dataclass
class MicrocreditPaymentReceived(DomainEvent):
    payment_id: str
    microcredit_id: str
    customer_id: str
    payment_amount: Dict[str, Any]
    payment_method: str
    payment_date: datetime
    is_on_time: bool
    days_late: int


@dataclass
class MicrocreditPaymentMissed(DomainEvent):
    microcredit_id: str
    customer_id: str
    missed_payment_id: str
    scheduled_amount: Dict[str, Any]
    scheduled_date: datetime
    days_overdue: int
    late_fee_applied: Dict[str, Any]


@dataclass
class MicrocreditDefaulted(DomainEvent):
    microcredit_id: str
    customer_id: str
    days_overdue: int
    outstanding_balance: Dict[str, Any]
    collection_actions_initiated: bool
    defaulted_at: datetime


@dataclass
class MicrocreditFullyPaid(DomainEvent):
    microcredit_id: str
    customer_id: str
    total_paid: Dict[str, Any]
    final_payment_date: datetime
    early_payment: bool
    days_early: int


@dataclass
class LateFeesApplied(DomainEvent):
    microcredit_id: str
    customer_id: str
    payment_id: str
    late_fee_amount: Dict[str, Any]
    days_late: int
    applied_at: datetime


@dataclass
class CreditLimitIncreased(DomainEvent):
    customer_id: str
    old_limit: Dict[str, Any]
    new_limit: Dict[str, Any]
    increase_reason: str
    approved_by: str
    effective_date: datetime


@dataclass
class CreditLimitDecreased(DomainEvent):
    customer_id: str
    old_limit: Dict[str, Any]
    new_limit: Dict[str, Any]
    decrease_reason: str
    approved_by: str
    effective_date: datetime


@dataclass
class CollectionActionInitiated(DomainEvent):
    microcredit_id: str
    customer_id: str
    action_type: str  # "phone_call", "sms", "email", "visit", "legal"
    action_details: str
    assigned_agent: str
    initiated_at: datetime


@dataclass
class PaymentReminderSent(DomainEvent):
    microcredit_id: str
    customer_id: str
    reminder_type: str  # "advance", "due_today", "overdue"
    channel: str  # "sms", "email", "whatsapp", "push"
    days_before_due: int
    sent_at: datetime


@dataclass
class CreditProfileUpdated(DomainEvent):
    customer_id: str
    profile_changes: Dict[str, Any]
    trigger_reason: str  # "payment_behavior", "new_data", "manual_update"
    updated_by: str
    updated_at: datetime


@dataclass
class FraudSuspicionDetected(DomainEvent):
    customer_id: str
    microcredit_id: Optional[str]
    fraud_indicators: List[str]
    risk_score: float
    auto_blocked: bool
    detected_at: datetime


@dataclass
class MicrocreditRefinanced(DomainEvent):
    original_microcredit_id: str
    new_microcredit_id: str
    customer_id: str
    refinance_amount: Dict[str, Any]
    new_terms: Dict[str, Any]
    refinanced_at: datetime


@dataclass
class InterestRateAdjusted(DomainEvent):
    microcredit_id: str
    customer_id: str
    old_rate: float
    new_rate: float
    adjustment_reason: str
    effective_date: datetime
    approved_by: str


@dataclass
class CreditScoreUpdated(DomainEvent):
    customer_id: str
    old_score: int
    new_score: int
    score_change: int
    update_triggers: List[str]
    updated_at: datetime


@dataclass
class PaymentMethodUpdated(DomainEvent):
    microcredit_id: str
    customer_id: str
    old_method: str
    new_method: str
    updated_by: str
    updated_at: datetime


@dataclass
class AutoPaymentSetup(DomainEvent):
    microcredit_id: str
    customer_id: str
    payment_method: str
    auto_payment_day: int
    amount_type: str  # "minimum", "full", "fixed"
    setup_at: datetime


@dataclass
class AutoPaymentFailed(DomainEvent):
    microcredit_id: str
    customer_id: str
    scheduled_amount: Dict[str, Any]
    failure_reason: str
    retry_scheduled: bool
    failed_at: datetime


@dataclass
class CreditApplicationWithdawn(DomainEvent):
    application_id: str
    customer_id: str
    withdrawal_reason: str
    withdrawn_by: str
    withdrawn_at: datetime


@dataclass
class MicrocreditSuspended(DomainEvent):
    microcredit_id: str
    customer_id: str
    suspension_reason: str
    suspended_by: str
    suspended_at: datetime
    reactivation_conditions: List[str]


@dataclass
class MicrocreditReactivated(DomainEvent):
    microcredit_id: str
    customer_id: str
    reactivation_reason: str
    conditions_met: List[str]
    reactivated_by: str
    reactivated_at: datetime


@dataclass
class CreditBureauReportGenerated(DomainEvent):
    customer_id: str
    report_type: str
    bureau_name: str
    credit_score: int
    report_reference: str
    generated_at: datetime


@dataclass
class RiskModelUpdated(DomainEvent):
    model_version: str
    previous_version: str
    model_type: str  # "credit_scoring", "fraud_detection", "collection"
    improvement_metrics: Dict[str, float]
    deployed_at: datetime
    deployed_by: str