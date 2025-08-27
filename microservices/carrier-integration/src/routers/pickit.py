"""
Pickit-specific API endpoints
Handles pickup points and last-mile delivery features
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import structlog

from ..carriers.pickit import PickitClient
from ..schemas import QuoteRequest, QuoteResponse, LabelRequest, LabelResponse, TrackingRequest, TrackingResponse
from ..error_handlers import CarrierException

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/pickit",
    tags=["Pickit"],
    responses={404: {"description": "Not found"}}
)


async def get_pickit_client() -> PickitClient:
    """Dependency to get Pickit client instance"""
    return PickitClient()


@router.get("/pickup-points")
async def get_pickup_points(
    latitude: float = Query(..., description="Latitude coordinate"),
    longitude: float = Query(..., description="Longitude coordinate"),
    radius_km: float = Query(5.0, description="Search radius in kilometers"),
    limit: int = Query(20, le=100, description="Maximum number of results"),
    client: PickitClient = Depends(get_pickit_client)
):
    """
    Get available Pickit pickup points near a location
    
    Returns list of pickup points with details including:
    - Location information
    - Opening hours
    - Available services
    - Capacity information
    """
    try:
        logger.info(
            "fetching_pickup_points",
            lat=latitude,
            lng=longitude,
            radius=radius_km
        )
        
        pickup_points = await client.get_pickup_points(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(pickup_points),
            "pickup_points": pickup_points
        }
        
    except CarrierException as e:
        logger.error(
            "pickup_points_error",
            error=str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "unexpected_error",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pickup points: {str(e)}"
        )


@router.get("/pickup-points/{point_id}")
async def get_pickup_point_details(
    point_id: str,
    client: PickitClient = Depends(get_pickit_client)
):
    """
    Get detailed information about a specific pickup point
    
    Returns:
    - Full address
    - Opening hours
    - Current capacity
    - Available services
    - Photos and additional information
    """
    try:
        # This would typically call a specific endpoint for pickup point details
        # For now, we'll implement a placeholder
        return {
            "status": "success",
            "pickup_point": {
                "id": point_id,
                "name": "Pickup Point Details",
                "type": "LOCKER",
                "address": {
                    "street": "123 Main St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "12345",
                    "country": "US"
                },
                "opening_hours": {
                    "monday": "08:00-20:00",
                    "tuesday": "08:00-20:00",
                    "wednesday": "08:00-20:00",
                    "thursday": "08:00-20:00",
                    "friday": "08:00-20:00",
                    "saturday": "09:00-18:00",
                    "sunday": "10:00-16:00"
                },
                "services": ["PACKAGE_PICKUP", "PACKAGE_DROP", "RETURNS"],
                "capacity": {
                    "small": 10,
                    "medium": 5,
                    "large": 2
                }
            }
        }
        
    except Exception as e:
        logger.error(
            "pickup_point_detail_error",
            point_id=point_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pickup point details: {str(e)}"
        )


@router.post("/shipments/{tracking_number}/proof-of-delivery")
async def get_proof_of_delivery(
    tracking_number: str,
    client: PickitClient = Depends(get_pickit_client)
):
    """
    Get proof of delivery for a Pickit shipment
    
    Returns:
    - Delivery timestamp
    - Signature (if available)
    - Delivery photo
    - Pickup code used (for pickup point deliveries)
    """
    try:
        logger.info(
            "fetching_proof_of_delivery",
            tracking_number=tracking_number
        )
        
        pod = await client.get_proof_of_delivery(tracking_number)
        
        return {
            "status": "success",
            "proof_of_delivery": pod
        }
        
    except CarrierException as e:
        logger.error(
            "pod_error",
            tracking_number=tracking_number,
            error=str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "unexpected_error",
            tracking_number=tracking_number,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch proof of delivery: {str(e)}"
        )


@router.post("/shipments/{tracking_number}/cancel")
async def cancel_shipment(
    tracking_number: str,
    reason: str = "",
    client: PickitClient = Depends(get_pickit_client)
):
    """
    Cancel a Pickit shipment
    
    Args:
        tracking_number: Shipment tracking number
        reason: Cancellation reason
    
    Returns:
        Cancellation confirmation
    """
    try:
        logger.info(
            "cancelling_shipment",
            tracking_number=tracking_number,
            reason=reason
        )
        
        result = await client.cancel_shipment(tracking_number, reason)
        
        return {
            "status": "success",
            "message": "Shipment cancelled successfully",
            "cancellation": result
        }
        
    except CarrierException as e:
        logger.error(
            "cancellation_error",
            tracking_number=tracking_number,
            error=str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "unexpected_error",
            tracking_number=tracking_number,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel shipment: {str(e)}"
        )


@router.get("/service-coverage")
async def check_service_coverage(
    postal_code: str = Query(..., description="Postal code to check"),
    city: str = Query(..., description="City name"),
    country: str = Query("US", description="Country code"),
    client: PickitClient = Depends(get_pickit_client)
):
    """
    Check if Pickit service is available in a specific area
    
    Returns:
    - Service availability
    - Available service types
    - Estimated transit times
    - Nearby pickup points count
    """
    try:
        # This would typically call a coverage check endpoint
        # For now, we'll return a mock response
        return {
            "status": "success",
            "coverage": {
                "postal_code": postal_code,
                "city": city,
                "country": country,
                "service_available": True,
                "service_types": ["STANDARD", "EXPRESS", "PICKUP_POINT"],
                "estimated_transit_days": {
                    "STANDARD": 2,
                    "EXPRESS": 1,
                    "PICKUP_POINT": 2
                },
                "nearby_pickup_points": 5
            }
        }
        
    except Exception as e:
        logger.error(
            "coverage_check_error",
            postal_code=postal_code,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check service coverage: {str(e)}"
        )


# Export router
__all__ = ["router"]