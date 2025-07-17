import asyncio
from typing import Dict, List, Callable, Any
from src.domain.events.base_event import DomainEvent, EventBus, EventHandler
from src.infrastructure.logging.logger import logger
import json

class InMemoryEventBus(EventBus):
    """Implementación en memoria del bus de eventos"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._async_handlers: Dict[str, List[Callable]] = {}
    
    async def publish(self, event: DomainEvent) -> None:
        """Publica un evento a todos los handlers suscritos"""
        event_type = event.get_event_type()
        
        # Log del evento
        logger.info(f"Publishing event: {event_type}", 
                   event_id=str(event.event_id),
                   aggregate_id=str(event.aggregate_id) if event.aggregate_id else None,
                   event_data=event.to_dict())
        
        # Enviar a handlers síncronos
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    await handler.handle(event)
                except Exception as e:
                    logger.error(f"Error handling event {event_type} with handler {handler.__class__.__name__}: {str(e)}")
        
        # Enviar a handlers asíncronos
        if event_type in self._async_handlers:
            tasks = []
            for handler_func in self._async_handlers[event_type]:
                try:
                    task = asyncio.create_task(handler_func(event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error creating task for event {event_type}: {str(e)}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Suscribe un handler a un tipo de evento"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.info(f"Handler {handler.__class__.__name__} subscribed to {event_type}")
    
    def subscribe_async(self, event_type: str, handler_func: Callable) -> None:
        """Suscribe una función asíncrona a un tipo de evento"""
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        
        self._async_handlers[event_type].append(handler_func)
        logger.info(f"Async handler {handler_func.__name__} subscribed to {event_type}")
    
    def get_subscribed_handlers(self, event_type: str) -> int:
        """Retorna el número de handlers suscritos a un evento"""
        sync_count = len(self._handlers.get(event_type, []))
        async_count = len(self._async_handlers.get(event_type, []))
        return sync_count + async_count

class EventStore:
    """Store para persistir eventos"""
    
    def __init__(self):
        self._events: List[Dict[str, Any]] = []
    
    async def save_event(self, event: DomainEvent) -> None:
        """Guarda un evento en el store"""
        event_data = event.to_dict()
        self._events.append(event_data)
        
        logger.info(f"Event saved to store: {event.get_event_type()}", 
                   event_id=str(event.event_id),
                   aggregate_id=str(event.aggregate_id) if event.aggregate_id else None)
    
    async def get_events_by_aggregate(self, aggregate_id: str, aggregate_type: str = None) -> List[Dict[str, Any]]:
        """Obtiene eventos por agregado"""
        events = [e for e in self._events if e.get('aggregate_id') == aggregate_id]
        
        if aggregate_type:
            events = [e for e in events if e.get('aggregate_type') == aggregate_type]
        
        return sorted(events, key=lambda x: x['occurred_at'])
    
    async def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Obtiene eventos por tipo"""
        return [e for e in self._events if e.get('event_type') == event_type]
    
    async def get_all_events(self, limit: int = None) -> List[Dict[str, Any]]:
        """Obtiene todos los eventos"""
        events = sorted(self._events, key=lambda x: x['occurred_at'], reverse=True)
        
        if limit:
            events = events[:limit]
        
        return events

# Instancia global del event bus
event_bus = InMemoryEventBus()
event_store = EventStore()

# Middleware para guardar eventos automáticamente
class EventStorageMiddleware:
    """Middleware que guarda automáticamente todos los eventos"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def handle(self, event: DomainEvent) -> None:
        await self.event_store.save_event(event)

# Registrar el middleware
storage_middleware = EventStorageMiddleware(event_store)
asyncio.create_task(event_bus.subscribe_async("*", storage_middleware.handle))