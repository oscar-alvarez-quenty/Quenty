from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from src.domain.value_objects.guide_id import GuideId

class IncidentType(Enum):
    DELIVERY_FAILED = "delivery_failed"
    RECIPIENT_NOT_FOUND = "recipient_not_found"
    WRONG_ADDRESS = "wrong_address"
    PACKAGE_DAMAGED = "package_damaged"
    PACKAGE_LOST = "package_lost"
    REFUSED_BY_RECIPIENT = "refused_by_recipient"
    SECURITY_ISSUE = "security_issue"
    WEATHER_DELAY = "weather_delay"
    VEHICLE_BREAKDOWN = "vehicle_breakdown"
    OTHER = "other"

class IncidentStatus(Enum):
    REPORTED = "reported"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class IncidentPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class IncidentEvidence:
    id: UUID = field(default_factory=uuid4)
    file_type: str = ""  # photo, document, audio
    file_url: str = ""
    file_name: str = ""
    description: str = ""
    uploaded_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Incident:
    id: UUID = field(default_factory=uuid4)
    guide_id: GuideId = None
    incident_type: IncidentType = IncidentType.OTHER
    priority: IncidentPriority = IncidentPriority.MEDIUM
    status: IncidentStatus = IncidentStatus.REPORTED
    title: str = ""
    description: str = ""
    location: str = ""
    reported_by: str = ""  # messenger, customer, system
    reporter_id: Optional[UUID] = None
    evidence: List[IncidentEvidence] = field(default_factory=list)
    resolution_notes: str = ""
    assigned_to: Optional[UUID] = None
    reported_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    estimated_resolution: Optional[datetime] = None
    
    def acknowledge(self, assigned_to: UUID) -> None:
        """Reconoce el incidente y lo asigna"""
        if self.status != IncidentStatus.REPORTED:
            raise ValueError("Only reported incidents can be acknowledged")
        
        self.status = IncidentStatus.IN_REVIEW
        self.assigned_to = assigned_to
        self.acknowledged_at = datetime.utcnow()
    
    def escalate(self, reason: str = "") -> None:
        """Escala el incidente"""
        if self.status not in [IncidentStatus.REPORTED, IncidentStatus.IN_REVIEW]:
            raise ValueError("Only reported or in-review incidents can be escalated")
        
        self.status = IncidentStatus.ESCALATED
        self.priority = IncidentPriority.HIGH
        if reason:
            self.resolution_notes += f"\nEscalated: {reason}"
    
    def resolve(self, resolution_notes: str) -> None:
        """Resuelve el incidente"""
        if self.status not in [IncidentStatus.IN_REVIEW, IncidentStatus.ESCALATED]:
            raise ValueError("Only in-review or escalated incidents can be resolved")
        
        self.status = IncidentStatus.RESOLVED
        self.resolution_notes = resolution_notes
        self.resolved_at = datetime.utcnow()
    
    def close(self) -> None:
        """Cierra el incidente"""
        if self.status != IncidentStatus.RESOLVED:
            raise ValueError("Only resolved incidents can be closed")
        
        self.status = IncidentStatus.CLOSED
        self.closed_at = datetime.utcnow()
    
    def add_evidence(self, file_type: str, file_url: str, file_name: str, description: str = "") -> None:
        """Agrega evidencia al incidente"""
        evidence = IncidentEvidence(
            file_type=file_type,
            file_url=file_url,
            file_name=file_name,
            description=description
        )
        self.evidence.append(evidence)
    
    def get_resolution_time_hours(self) -> Optional[float]:
        """Calcula el tiempo de resolución en horas"""
        if not self.resolved_at:
            return None
        
        delta = self.resolved_at - self.reported_at
        return delta.total_seconds() / 3600

@dataclass
class DeliveryAttempt:
    id: UUID = field(default_factory=uuid4)
    guide_id: GuideId = None
    attempt_number: int = 1
    attempted_at: datetime = field(default_factory=datetime.utcnow)
    status: str = ""  # successful, failed, rescheduled
    failure_reason: Optional[IncidentType] = None
    notes: str = ""
    next_attempt_scheduled: Optional[datetime] = None
    messenger_id: Optional[UUID] = None
    location: str = ""
    recipient_contacted: bool = False
    
    def mark_successful(self, notes: str = "") -> None:
        """Marca el intento como exitoso"""
        self.status = "successful"
        self.notes = notes
    
    def mark_failed(self, reason: IncidentType, notes: str = "") -> None:
        """Marca el intento como fallido"""
        self.status = "failed"
        self.failure_reason = reason
        self.notes = notes
    
    def reschedule(self, next_attempt: datetime, notes: str = "") -> None:
        """Reprograma el intento de entrega"""
        self.status = "rescheduled"
        self.next_attempt_scheduled = next_attempt
        self.notes = notes

@dataclass
class DeliveryRetry:
    id: UUID = field(default_factory=uuid4)
    guide_id: GuideId = None
    original_incident_id: UUID = None
    retry_reason: str = ""
    max_attempts: int = 3
    current_attempt: int = 0
    attempts: List[DeliveryAttempt] = field(default_factory=list)
    final_status: str = ""  # delivered, returned_to_sender, abandoned
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def add_attempt(self, attempt: DeliveryAttempt) -> None:
        """Agrega un intento de entrega"""
        if self.current_attempt >= self.max_attempts:
            raise ValueError("Maximum delivery attempts reached")
        
        self.current_attempt += 1
        attempt.attempt_number = self.current_attempt
        self.attempts.append(attempt)
    
    def complete_delivery(self) -> None:
        """Completa la entrega exitosamente"""
        if not self.attempts or self.attempts[-1].status != "successful":
            raise ValueError("Cannot complete delivery without successful attempt")
        
        self.final_status = "delivered"
        self.completed_at = datetime.utcnow()
    
    def return_to_sender(self, reason: str = "") -> None:
        """Retorna el paquete al remitente"""
        if self.current_attempt < self.max_attempts:
            raise ValueError("Cannot return to sender before exhausting all attempts")
        
        self.final_status = "returned_to_sender"
        self.completed_at = datetime.utcnow()
        if reason:
            self.retry_reason += f"\nReturned: {reason}"
    
    def has_remaining_attempts(self) -> bool:
        """Verifica si quedan intentos disponibles"""
        return self.current_attempt < self.max_attempts