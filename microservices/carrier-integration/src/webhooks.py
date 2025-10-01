from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any
import structlog
from datetime import datetime
from sqlalchemy.orm import Session

from .database import get_db
from .models import TrackingEvent as TrackingEventModel, CarrierType
from .schemas import TrackingEvent

logger = structlog.get_logger()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/dhl/tracking")
async def dhl_tracking_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle DHL tracking update webhooks"""
    try:
        data = await request.json()
        logger.info("DHL tracking webhook received", data=data)
        
        # Parse DHL webhook format
        tracking_number = data.get('trackingNumber')
        events = data.get('events', [])
        
        for event in events:
            # Save tracking event to database
            db_event = TrackingEventModel(
                tracking_number=tracking_number,
                carrier=CarrierType.DHL,
                event_date=datetime.fromisoformat(event['timestamp']),
                status=event['statusCode'],
                description=event['description'],
                location=event.get('location', {}).get('address', {}).get('addressLocality'),
                raw_data=event
            )
            db.add(db_event)
        
        db.commit()
        
        # TODO: Notify relevant services about tracking update
        await _notify_tracking_update(tracking_number, "DHL", data)
        
        return {"status": "success", "message": "Tracking update processed"}
        
    except Exception as e:
        logger.error("Failed to process DHL webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fedex/tracking")
async def fedex_tracking_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle FedEx tracking update webhooks"""
    try:
        data = await request.json()
        logger.info("FedEx tracking webhook received", data=data)
        
        # Parse FedEx webhook format
        tracking_info = data.get('trackingInfo', {})
        tracking_number = tracking_info.get('trackingNumber')
        events = tracking_info.get('scanEvents', [])
        
        for event in events:
            # Save tracking event to database
            db_event = TrackingEventModel(
                tracking_number=tracking_number,
                carrier=CarrierType.FEDEX,
                event_date=datetime.fromisoformat(event['date']),
                status=event['derivedStatus'],
                description=event['eventDescription'],
                location=event.get('scanLocation'),
                raw_data=event
            )
            db.add(db_event)
        
        db.commit()
        
        await _notify_tracking_update(tracking_number, "FedEx", data)
        
        return {"status": "success", "message": "Tracking update processed"}
        
    except Exception as e:
        logger.error("Failed to process FedEx webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ups/quantum-view")
async def ups_quantum_view_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle UPS Quantum View webhooks for tracking updates"""
    try:
        data = await request.json()
        logger.info("UPS Quantum View webhook received", data=data)
        
        # Parse UPS Quantum View format
        shipments = data.get('QuantumViewEvents', {}).get('SubscriptionEvents', [])
        
        for shipment in shipments:
            tracking_number = shipment.get('TrackingNumber')
            events = shipment.get('Activity', [])
            
            for event in events:
                # Save tracking event to database
                db_event = TrackingEventModel(
                    tracking_number=tracking_number,
                    carrier=CarrierType.UPS,
                    event_date=datetime.strptime(
                        f"{event['Date']} {event['Time']}",
                        "%Y%m%d %H%M%S"
                    ),
                    status=event['Status']['Type'],
                    description=event['Status']['Description'],
                    location=event.get('ActivityLocation', {}).get('Address', {}).get('City'),
                    raw_data=event
                )
                db.add(db_event)
        
        db.commit()
        
        return {"status": "success", "message": "Quantum View update processed"}
        
    except Exception as e:
        logger.error("Failed to process UPS webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servientrega/notifications")
async def servientrega_notification_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Servientrega notification webhooks"""
    try:
        data = await request.json()
        logger.info("Servientrega notification webhook received", data=data)
        
        # Parse Servientrega webhook format
        guia = data.get('NumeroGuia')
        estado = data.get('Estado')
        fecha = data.get('Fecha')
        ciudad = data.get('Ciudad')
        descripcion = data.get('Descripcion')
        
        # Save tracking event to database
        db_event = TrackingEventModel(
            tracking_number=guia,
            carrier=CarrierType.SERVIENTREGA,
            event_date=datetime.fromisoformat(fecha),
            status=estado,
            description=descripcion,
            location=ciudad,
            raw_data=data
        )
        db.add(db_event)
        db.commit()
        
        await _notify_tracking_update(guia, "Servientrega", data)
        
        return {"status": "success", "message": "Notification processed"}
        
    except Exception as e:
        logger.error("Failed to process Servientrega webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interrapidisimo/events")
async def interrapidisimo_event_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Interrapidisimo event webhooks"""
    try:
        data = await request.json()
        logger.info("Interrapidisimo event webhook received", data=data)
        
        # Parse Interrapidisimo webhook format
        evento = data.get('evento', {})
        remesa = evento.get('numeroRemesa')
        tipo_evento = evento.get('tipoEvento')
        fecha = evento.get('fecha')
        ubicacion = evento.get('ubicacion')
        descripcion = evento.get('descripcion')
        
        # Save tracking event to database
        db_event = TrackingEventModel(
            tracking_number=remesa,
            carrier=CarrierType.INTERRAPIDISIMO,
            event_date=datetime.fromisoformat(fecha),
            status=tipo_evento,
            description=descripcion,
            location=ubicacion,
            raw_data=data
        )
        db.add(db_event)
        db.commit()
        
        await _notify_tracking_update(remesa, "Interrapidisimo", data)
        
        return {"status": "success", "message": "Event processed"}
        
    except Exception as e:
        logger.error("Failed to process Interrapidisimo webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pickit/events")
async def pickit_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Pickit tracking and pickup point events"""
    try:
        # Get webhook headers for validation
        signature = request.headers.get("X-Pickit-Signature")
        timestamp = request.headers.get("X-Pickit-Timestamp")
        
        # Get raw body for signature validation
        body = await request.body()
        data = await request.json()
        
        logger.info("Pickit webhook received", event_type=data.get("event_type"))
        
        # Validate webhook signature
        from .carriers.pickit import PickitClient
        client = PickitClient()
        
        if signature and timestamp:
            is_valid = await client.validate_webhook(body.decode(), signature, timestamp)
            if not is_valid:
                logger.warning("Invalid Pickit webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process webhook event
        event_type = data.get("event_type")
        event_data = data.get("data", {})
        
        # Process the event using the Pickit client
        result = await client.process_webhook(event_type, event_data)
        
        # Handle different event types
        if event_type in ["shipment.in_transit", "shipment.at_pickup_point", "shipment.delivered"]:
            tracking_number = event_data.get("tracking_number")
            
            # Save tracking event to database
            db_event = TrackingEventModel(
                tracking_number=tracking_number,
                carrier=CarrierType.PICKIT,
                event_date=datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat())),
                status=result.get("status"),
                description=event_data.get("description", event_type),
                location=event_data.get("location"),
                raw_data=data
            )
            db.add(db_event)
            db.commit()
            
            # Notify about tracking update
            await _notify_tracking_update(tracking_number, "Pickit", result)
            
            # Special handling for delivery
            if event_type == "shipment.delivered":
                await _notify_delivery_confirmation(tracking_number, "Pickit", result)
        
        elif event_type == "shipment.at_pickup_point":
            # Notify customer about package arrival at pickup point
            logger.info(
                "Package arrived at pickup point",
                tracking_number=event_data.get("tracking_number"),
                pickup_code=result.get("pickup_code")
            )
            # TODO: Send notification with pickup code
        
        return {"status": "success", "message": f"Event {event_type} processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process Pickit webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dhl/pod")
async def dhl_proof_of_delivery_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle DHL Proof of Delivery webhooks"""
    try:
        data = await request.json()
        logger.info("DHL POD webhook received", data=data)
        
        tracking_number = data.get('trackingNumber')
        pod_data = data.get('proofOfDelivery', {})
        
        # Update tracking with delivery confirmation
        db_event = TrackingEventModel(
            tracking_number=tracking_number,
            carrier=CarrierType.DHL,
            event_date=datetime.fromisoformat(data.get('deliveryDate')),
            status="DELIVERED",
            description=f"Delivered to {pod_data.get('signedBy', 'recipient')}",
            location=data.get('deliveryLocation'),
            raw_data=data
        )
        db.add(db_event)
        db.commit()
        
        # Notify about successful delivery
        await _notify_delivery_confirmation(tracking_number, "DHL", pod_data)
        
        return {"status": "success", "message": "POD processed"}
        
    except Exception as e:
        logger.error("Failed to process DHL POD webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def _notify_tracking_update(
    tracking_number: str,
    carrier: str,
    data: Dict[str, Any]
):
    """Notify relevant services about tracking updates"""
    try:
        # TODO: Implement notification to order service
        # This could use message queue (RabbitMQ) or direct HTTP call
        logger.info("Notifying tracking update",
                   tracking_number=tracking_number,
                   carrier=carrier)
        
        # Example: Send to RabbitMQ
        # await publish_message("tracking.updates", {
        #     "tracking_number": tracking_number,
        #     "carrier": carrier,
        #     "data": data,
        #     "timestamp": datetime.now().isoformat()
        # })
        
    except Exception as e:
        logger.error("Failed to notify tracking update", error=str(e))


async def _notify_delivery_confirmation(
    tracking_number: str,
    carrier: str,
    pod_data: Dict[str, Any]
):
    """Notify about successful delivery with proof"""
    try:
        logger.info("Notifying delivery confirmation",
                   tracking_number=tracking_number,
                   carrier=carrier)
        
        # TODO: Implement notification logic
        # - Update order status
        # - Send customer notification
        # - Trigger payment settlement if COD
        
    except Exception as e:
        logger.error("Failed to notify delivery confirmation", error=str(e))


# Webhook registration endpoints (for carriers that require registration)
@router.post("/register/{carrier}")
async def register_webhook(
    carrier: str,
    webhook_url: str,
    events: list[str]
):
    """Register webhook URL with carrier"""
    try:
        logger.info("Registering webhook",
                   carrier=carrier,
                   webhook_url=webhook_url,
                   events=events)
        
        # TODO: Implement carrier-specific webhook registration
        # Each carrier has different registration process
        
        if carrier.upper() == "FEDEX":
            # FedEx webhook registration
            pass
        elif carrier.upper() == "UPS":
            # UPS Quantum View subscription
            pass
        
        return {
            "status": "success",
            "message": f"Webhook registered for {carrier}",
            "webhook_url": webhook_url,
            "events": events
        }
        
    except Exception as e:
        logger.error("Failed to register webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unregister/{carrier}")
async def unregister_webhook(carrier: str):
    """Unregister webhook with carrier"""
    try:
        logger.info("Unregistering webhook", carrier=carrier)
        
        # TODO: Implement carrier-specific webhook unregistration
        
        return {
            "status": "success",
            "message": f"Webhook unregistered for {carrier}"
        }
        
    except Exception as e:
        logger.error("Failed to unregister webhook", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))