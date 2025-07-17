from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

@dataclass
class DomainEvent(ABC):
    """Clase base para todos los eventos de dominio"""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = None
    aggregate_type: str = ""
    event_version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def get_event_type(self) -> str:
        """Retorna el tipo de evento"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario para serialización"""
        return {
            "event_id": str(self.event_id),
            "event_type": self.get_event_type(),
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": str(self.aggregate_id) if self.aggregate_id else None,
            "aggregate_type": self.aggregate_type,
            "event_version": self.event_version,
            "metadata": self.metadata,
            "data": self._get_event_data()
        }
    
    @abstractmethod
    def _get_event_data(self) -> Dict[str, Any]:
        """Retorna los datos específicos del evento"""
        pass

class EventBus(ABC):
    """Interfaz para el bus de eventos"""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publica un evento"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler) -> None:
        """Suscribe un handler a un tipo de evento"""
        pass

class EventHandler(ABC):
    """Clase base para manejadores de eventos"""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Maneja un evento de dominio"""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Verifica si puede manejar un tipo de evento"""
        pass