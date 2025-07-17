from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.domain.entities.pickup import PickupType, PickupStatus


class PickupTimeSlotRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    max_pickups: int = 10
    
    @validator('end_time')
    def validate_end_time_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('max_pickups')
    def validate_max_pickups_positive(cls, v):
        if v <= 0:
            raise ValueError('Max pickups must be positive')
        return v


class PickupRequestCreate(BaseModel):
    guide_id: str
    customer_id: str
    pickup_type: PickupType
    pickup_address: str
    contact_name: str
    contact_phone: str
    priority: str = "normal"
    estimated_packages: int = 1
    total_weight_kg: Optional[float] = None
    special_instructions: Optional[str] = None
    
    @validator('pickup_address', 'contact_name', 'contact_phone')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ["low", "normal", "high", "urgent"]
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v
    
    @validator('estimated_packages')
    def validate_estimated_packages_positive(cls, v):
        if v <= 0:
            raise ValueError('Estimated packages must be positive')
        return v


class PickupSchedule(BaseModel):
    pickup_id: str
    scheduled_date: datetime
    time_slot: PickupTimeSlotRequest
    operator_id: str


class PickupReschedule(BaseModel):
    pickup_id: str
    new_scheduled_date: datetime
    new_time_slot: PickupTimeSlotRequest
    reschedule_reason: str
    
    @validator('reschedule_reason')
    def validate_reschedule_reason_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Reschedule reason cannot be empty')
        return v.strip()


class PickupCancel(BaseModel):
    pickup_id: str
    cancellation_reason: str
    cancelled_by: str
    
    @validator('cancellation_reason', 'cancelled_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class PickupComplete(BaseModel):
    pickup_id: str
    operator_id: str
    completion_notes: str
    evidence_urls: Optional[List[str]] = None
    
    @validator('completion_notes')
    def validate_completion_notes_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Completion notes cannot be empty')
        return v.strip()


class PickupFail(BaseModel):
    pickup_id: str
    operator_id: str
    failure_reason: str
    notes: Optional[str] = None
    
    @validator('failure_reason')
    def validate_failure_reason_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Failure reason cannot be empty')
        return v.strip()


class PickupRouteCreate(BaseModel):
    operator_id: str
    scheduled_date: datetime
    pickup_ids: Optional[List[str]] = None


class PickupRequestResponse(BaseModel):
    pickup_id: str
    guide_id: str
    customer_id: str
    pickup_type: PickupType
    pickup_address: str
    contact_name: str
    contact_phone: str
    status: PickupStatus
    priority: str
    estimated_packages: int
    total_weight_kg: Optional[float]
    special_instructions: Optional[str]
    scheduled_date: Optional[datetime]
    assigned_operator_id: Optional[str]
    assigned_point_id: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    is_overdue: bool
    can_be_rescheduled: bool
    
    class Config:
        from_attributes = True


class PickupAttemptResponse(BaseModel):
    attempt_id: str
    pickup_id: str
    status: str
    attempted_by: str
    attempted_at: datetime
    notes: Optional[str]
    failure_reason: Optional[str]
    evidence_urls: Optional[List[str]]
    
    class Config:
        from_attributes = True


class PickupRouteResponse(BaseModel):
    route_id: str
    operator_id: str
    scheduled_date: datetime
    status: str
    pickup_requests: List[PickupRequestResponse]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_pickups: int
    completed_pickups: int
    failed_pickups: int
    success_rate: float
    estimated_duration_hours: Optional[float]
    actual_duration_hours: Optional[float]
    
    class Config:
        from_attributes = True


class PickupMetricsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_pickups: int
    completed_pickups: int
    failed_pickups: int
    cancelled_pickups: int
    success_rate: float
    average_completion_time_hours: float
    overdue_pickups: int
    operator_performance: Dict[str, Any]


class PickupSummaryResponse(BaseModel):
    pickup_id: str
    guide_id: str
    status: str
    priority: str
    pickup_address: str
    contact_name: str
    scheduled_date: Optional[datetime]
    is_overdue: bool
    can_be_rescheduled: bool
    special_instructions: Optional[str]
    
    class Config:
        from_attributes = True