from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.domain.entities.analytics import ReportType, MetricType, DashboardStatus


class DashboardCreate(BaseModel):
    name: str
    description: str
    created_by: str
    permissions: str = "private"
    
    @validator('name', 'description', 'created_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = ['private', 'public', 'restricted']
        if v.lower() not in valid_permissions:
            raise ValueError(f'Permissions must be one of: {valid_permissions}')
        return v.lower()


class WidgetCreate(BaseModel):
    dashboard_id: str
    title: str
    widget_type: str
    data_source: str
    configuration: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, int]] = None
    
    @validator('dashboard_id', 'title', 'widget_type', 'data_source')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('widget_type')
    def validate_widget_type(cls, v):
        valid_types = ['chart', 'table', 'metric', 'gauge', 'map', 'text']
        if v.lower() not in valid_types:
            raise ValueError(f'Widget type must be one of: {valid_types}')
        return v.lower()


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, int]] = None
    is_enabled: Optional[bool] = None
    
    @validator('title')
    def validate_title_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v


class DashboardLayoutUpdate(BaseModel):
    dashboard_id: str
    layout_config: Dict[str, Any]
    
    @validator('dashboard_id')
    def validate_dashboard_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Dashboard ID cannot be empty')
        return v.strip()


class ReportDefinitionCreate(BaseModel):
    name: str
    report_type: str
    description: str
    data_sources: List[str]
    template_path: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    @validator('name', 'description')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('report_type')
    def validate_report_type(cls, v):
        valid_types = ['scheduled', 'on_demand', 'automated']
        if v.lower() not in valid_types:
            raise ValueError(f'Report type must be one of: {valid_types}')
        return v.lower()
    
    @validator('data_sources')
    def validate_data_sources_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one data source is required')
        for source in v:
            if not source or not source.strip():
                raise ValueError('Data sources cannot be empty')
        return [source.strip() for source in v]


class ReportSchedule(BaseModel):
    report_id: str
    frequency: str
    time_of_day: str
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    timezone: str = "UTC"
    
    @validator('report_id', 'frequency', 'time_of_day', 'timezone')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('frequency')
    def validate_frequency(cls, v):
        valid_frequencies = ['daily', 'weekly', 'monthly', 'yearly']
        if v.lower() not in valid_frequencies:
            raise ValueError(f'Frequency must be one of: {valid_frequencies}')
        return v.lower()
    
    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if v is not None and not 0 <= v <= 6:
            raise ValueError('Day of week must be between 0 (Monday) and 6 (Sunday)')
        return v
    
    @validator('day_of_month')
    def validate_day_of_month(cls, v):
        if v is not None and not 1 <= v <= 31:
            raise ValueError('Day of month must be between 1 and 31')
        return v


class ReportExecute(BaseModel):
    report_id: str
    parameters: Optional[Dict[str, Any]] = None
    output_format: str = "pdf"
    
    @validator('report_id')
    def validate_report_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Report ID cannot be empty')
        return v.strip()
    
    @validator('output_format')
    def validate_output_format(cls, v):
        valid_formats = ['pdf', 'excel', 'csv', 'html']
        if v.lower() not in valid_formats:
            raise ValueError(f'Output format must be one of: {valid_formats}')
        return v.lower()


class MetricDefinitionCreate(BaseModel):
    name: str
    description: str
    metric_type: str
    unit: str
    tags: Optional[Dict[str, str]] = None
    retention_days: int = 90
    
    @validator('name', 'description', 'unit')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('metric_type')
    def validate_metric_type(cls, v):
        valid_types = ['counter', 'gauge', 'histogram', 'summary']
        if v.lower() not in valid_types:
            raise ValueError(f'Metric type must be one of: {valid_types}')
        return v.lower()
    
    @validator('retention_days')
    def validate_retention_days_positive(cls, v):
        if v <= 0:
            raise ValueError('Retention days must be positive')
        return v


class MetricValueRecord(BaseModel):
    metric_name: str
    value: float
    tags: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None
    
    @validator('metric_name')
    def validate_metric_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Metric name cannot be empty')
        return v.strip()


class KPICreate(BaseModel):
    name: str
    description: str
    target_value: float
    unit: str
    category: Optional[str] = None
    
    @validator('name', 'description', 'unit')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('target_value')
    def validate_target_value_positive(cls, v):
        if v <= 0:
            raise ValueError('Target value must be positive')
        return v


class KPIUpdate(BaseModel):
    kpi_id: str
    new_value: float
    
    @validator('kpi_id')
    def validate_kpi_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('KPI ID cannot be empty')
        return v.strip()


class KPITargetUpdate(BaseModel):
    kpi_id: str
    new_target: float
    reason: str
    
    @validator('kpi_id', 'reason')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('new_target')
    def validate_new_target_positive(cls, v):
        if v <= 0:
            raise ValueError('New target must be positive')
        return v


class DashboardResponse(BaseModel):
    dashboard_id: str
    name: str
    description: str
    created_by: str
    status: str
    permissions: str
    widgets_count: int
    created_at: datetime
    layout: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class WidgetResponse(BaseModel):
    widget_id: str
    title: str
    widget_type: str
    data_source: str
    is_enabled: bool
    position: Dict[str, int]
    configuration: Dict[str, Any]
    created_at: datetime
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReportDefinitionResponse(BaseModel):
    report_id: str
    name: str
    report_type: str
    description: str
    created_by: str
    is_active: bool
    data_sources: List[str]
    parameters: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportExecutionResponse(BaseModel):
    execution_id: str
    report_id: str
    status: str
    requested_by: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    execution_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class MetricDefinitionResponse(BaseModel):
    metric_id: str
    name: str
    description: str
    metric_type: str
    unit: str
    tags: Dict[str, str]
    retention_days: int
    created_at: datetime
    last_recorded: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class KPIResponse(BaseModel):
    kpi_id: str
    name: str
    description: str
    target_value: float
    current_value: Optional[float] = None
    unit: str
    status: str
    trend: Optional[str] = None
    performance_percentage: Optional[float] = None
    category: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MetricsSummaryResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Any]
    total_metrics: int
    data_points: int
    
    class Config:
        from_attributes = True


class KPIDashboardResponse(BaseModel):
    total_kpis: int
    on_target: int
    below_target: int
    above_target: int
    performance_rate: float
    kpis: List[Dict[str, Any]]
    last_updated: datetime
    
    class Config:
        from_attributes = True


class DashboardSummaryResponse(BaseModel):
    dashboard_id: str
    name: str
    widgets: List[WidgetResponse]
    performance_data: Dict[str, Any]
    last_refreshed: datetime
    
    class Config:
        from_attributes = True


class ReportStatusResponse(BaseModel):
    total_reports: int
    active_reports: int
    scheduled_reports: int
    on_demand_reports: int
    recent_executions: List[ReportExecutionResponse]
    
    class Config:
        from_attributes = True