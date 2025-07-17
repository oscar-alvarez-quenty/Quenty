from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.domain.events.base_event import DomainEvent


@dataclass
class DashboardCreated(DomainEvent):
    dashboard_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime


@dataclass
class DashboardUpdated(DomainEvent):
    dashboard_id: str
    updated_fields: List[str]
    updated_by: str
    updated_at: datetime


@dataclass
class WidgetAdded(DomainEvent):
    dashboard_id: str
    widget_id: str
    widget_type: str
    title: str
    added_by: str
    added_at: datetime


@dataclass
class WidgetRemoved(DomainEvent):
    dashboard_id: str
    widget_id: str
    removed_by: str
    removed_at: datetime


@dataclass
class WidgetConfigurationUpdated(DomainEvent):
    dashboard_id: str
    widget_id: str
    configuration_changes: Dict[str, Any]
    updated_by: str
    updated_at: datetime


@dataclass
class DashboardAccessed(DomainEvent):
    dashboard_id: str
    user_id: str
    access_type: str  # "view", "edit", "share"
    accessed_at: datetime
    session_duration_seconds: Optional[int] = None


@dataclass
class ReportDefinitionCreated(DomainEvent):
    report_id: str
    name: str
    report_type: str
    created_by: str
    created_at: datetime


@dataclass
class ReportScheduled(DomainEvent):
    report_id: str
    frequency: str
    scheduled_by: str
    next_run_time: datetime
    scheduled_at: datetime


@dataclass
class ReportExecutionStarted(DomainEvent):
    execution_id: str
    report_id: str
    report_name: str
    requested_by: str
    parameters: Dict[str, Any]
    started_at: datetime


@dataclass
class ReportExecutionCompleted(DomainEvent):
    execution_id: str
    report_id: str
    execution_time_seconds: float
    file_size_bytes: int
    output_format: str
    completed_at: datetime


@dataclass
class ReportExecutionFailed(DomainEvent):
    execution_id: str
    report_id: str
    error_message: str
    execution_time_seconds: float
    failed_at: datetime


@dataclass
class ReportDownloaded(DomainEvent):
    execution_id: str
    report_id: str
    downloaded_by: str
    download_method: str  # "direct", "email", "api"
    downloaded_at: datetime


@dataclass
class MetricRegistered(DomainEvent):
    metric_id: str
    metric_name: str
    metric_type: str
    unit: str
    retention_days: int
    registered_by: str
    registered_at: datetime


@dataclass
class MetricValueRecorded(DomainEvent):
    metric_id: str
    value: float
    tags: Dict[str, str]
    recorded_at: datetime


@dataclass
class MetricThresholdExceeded(DomainEvent):
    metric_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    threshold_type: str  # "upper", "lower"
    severity: str  # "warning", "critical"
    detected_at: datetime


@dataclass
class KPICreated(DomainEvent):
    kpi_id: str
    name: str
    target_value: float
    unit: str
    created_by: str
    created_at: datetime


@dataclass
class KPIUpdated(DomainEvent):
    kpi_id: str
    old_value: Optional[float]
    new_value: float
    target_value: float
    status: str  # "on_target", "below_target", "above_target"
    trend: str  # "up", "down", "stable"
    updated_at: datetime


@dataclass
class KPITargetAchieved(DomainEvent):
    kpi_id: str
    kpi_name: str
    achieved_value: float
    target_value: float
    achievement_percentage: float
    achieved_at: datetime


@dataclass
class KPITargetMissed(DomainEvent):
    kpi_id: str
    kpi_name: str
    current_value: float
    target_value: float
    gap_percentage: float
    period_end: datetime


@dataclass
class AnalyticsAlertTriggered(DomainEvent):
    alert_id: str
    alert_type: str  # "metric_threshold", "kpi_target", "report_failure"
    severity: str
    message: str
    affected_entities: List[str]
    triggered_at: datetime


@dataclass
class DataQualityIssueDetected(DomainEvent):
    issue_id: str
    data_source: str
    issue_type: str  # "missing_data", "invalid_data", "duplicate_data"
    affected_records: int
    issue_description: str
    detected_at: datetime


@dataclass
class AnalyticsJobStarted(DomainEvent):
    job_id: str
    job_type: str  # "data_processing", "metric_calculation", "report_generation"
    data_sources: List[str]
    estimated_duration_minutes: Optional[int]
    started_at: datetime


@dataclass
class AnalyticsJobCompleted(DomainEvent):
    job_id: str
    job_type: str
    processing_time_seconds: float
    records_processed: int
    records_failed: int
    completed_at: datetime


@dataclass
class AnalyticsJobFailed(DomainEvent):
    job_id: str
    job_type: str
    failure_reason: str
    processing_time_seconds: float
    failed_at: datetime
    retry_scheduled: bool


@dataclass
class CustomAnalyticsQueryExecuted(DomainEvent):
    query_id: str
    user_id: str
    query_type: str
    execution_time_ms: int
    records_returned: int
    executed_at: datetime


@dataclass
class AnalyticsPermissionGranted(DomainEvent):
    resource_type: str  # "dashboard", "report", "metric"
    resource_id: str
    user_id: str
    permissions: List[str]
    granted_by: str
    granted_at: datetime


@dataclass
class AnalyticsPermissionRevoked(DomainEvent):
    resource_type: str
    resource_id: str
    user_id: str
    permissions: List[str]
    revoked_by: str
    revoked_at: datetime


@dataclass
class AnalyticsDataExported(DomainEvent):
    export_id: str
    export_type: str  # "dashboard", "report", "raw_data"
    resource_id: str
    format: str  # "csv", "excel", "json", "pdf"
    file_size_bytes: int
    exported_by: str
    exported_at: datetime


@dataclass
class AnalyticsConfigurationChanged(DomainEvent):
    configuration_type: str  # "retention_policy", "alert_threshold", "refresh_interval"
    resource_id: str
    old_configuration: Dict[str, Any]
    new_configuration: Dict[str, Any]
    changed_by: str
    changed_at: datetime


@dataclass
class AnalyticsPerformanceOptimized(DomainEvent):
    optimization_type: str  # "query_optimization", "index_creation", "data_compression"
    affected_resources: List[str]
    performance_improvement_percentage: float
    optimized_by: str
    optimized_at: datetime


@dataclass
class AnalyticsSystemHealthCheck(DomainEvent):
    check_id: str
    system_status: str  # "healthy", "degraded", "critical"
    components_checked: List[str]
    issues_found: List[str]
    response_time_ms: int
    checked_at: datetime


@dataclass
class AnalyticsCapacityAlert(DomainEvent):
    resource_type: str  # "storage", "compute", "memory"
    current_usage_percentage: float
    threshold_percentage: float
    estimated_time_to_full: Optional[int]  # hours
    alert_severity: str
    detected_at: datetime


@dataclass
class AnalyticsBackupCompleted(DomainEvent):
    backup_id: str
    backup_type: str  # "full", "incremental", "differential"
    data_sources: List[str]
    backup_size_bytes: int
    backup_duration_seconds: int
    backup_location: str
    completed_at: datetime


@dataclass
class AnalyticsRestoreRequested(DomainEvent):
    restore_id: str
    backup_id: str
    restore_point: datetime
    requested_by: str
    requested_at: datetime


@dataclass
class AnalyticsAuditTrailGenerated(DomainEvent):
    audit_id: str
    audit_period_start: datetime
    audit_period_end: datetime
    activities_audited: int
    compliance_issues: List[str]
    generated_by: str
    generated_at: datetime