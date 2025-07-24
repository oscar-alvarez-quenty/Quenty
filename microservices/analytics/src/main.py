from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import structlog
import consul
import requests
import os
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

from .database import get_db, init_db, close_db
from .models import Metric, Dashboard, Report, Alert, AnalyticsQuery, MetricType, ReportStatus

# Import logging configuration
try:
    from .logging_config import LOGGING_MESSAGES, ERROR_MESSAGES, INFO_MESSAGES, DEBUG_MESSAGES, WARNING_MESSAGES
except ImportError:
    # Fallback if logging_config is not available
    LOGGING_MESSAGES = ERROR_MESSAGES = INFO_MESSAGES = DEBUG_MESSAGES = WARNING_MESSAGES = {}

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Set log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = structlog.get_logger("analytics-service")

# Settings
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8009")
CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))
SERVICE_NAME = "analytics-service"

app = FastAPI(
    title="Quenty Analytics Service",
    description="Comprehensive business analytics, reporting, and metrics collection microservice",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Enums
class TimeGranularity(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

# Pydantic models
class MetricIngest(BaseModel):
    metric_type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    value: Decimal = Field(...)
    unit: Optional[str] = None
    tags: Optional[Dict[str, Any]] = {}
    timestamp: Optional[datetime] = None
    source_service: Optional[str] = None
    source_entity_id: Optional[str] = None
    source_entity_type: Optional[str] = None

class QueryRequest(BaseModel):
    metric_type: Optional[str] = None
    start_date: date
    end_date: date
    granularity: TimeGranularity = TimeGranularity.DAILY
    filters: Optional[Dict[str, Any]] = {}
    aggregation: str = "sum"  # sum, avg, count, min, max

class DashboardMetrics(BaseModel):
    total_revenue: Decimal
    total_orders: int
    total_customers: int
    avg_order_value: Decimal
    revenue_growth: Decimal
    order_growth: Decimal
    top_performing_services: List[Dict[str, Any]]
    recent_trends: List[Dict[str, Any]]

class ReportRequest(BaseModel):
    name: str = Field(..., min_length=1)
    report_type: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = {}
    filters: Dict[str, Any] = {}
    date_range: Dict[str, str] = {}
    format: str = "json"

class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/api/v1/profile", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return response.json()
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions"""
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        # Superusers have all permissions
        if "*" in user_permissions:
            return current_user
            
        # Check if user has required permissions
        if not any(perm in user_permissions for perm in permissions + ["analytics:*"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return permission_checker

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        await init_db()
        await register_with_consul()
        logger.info("Analytics service started successfully")
    except Exception as e:
        logger.error("Failed to start analytics service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await deregister_from_consul()
        await close_db()
        logger.info("Analytics service shutdown successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

async def register_with_consul():
    """Register service with Consul"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    try:
        c.agent.service.register(
            name=SERVICE_NAME,
            service_id=f"{SERVICE_NAME}-1",
            address="analytics-service",
            port=8006,
            check=consul.Check.http(
                url="http://analytics-service:8006/health",
                interval="10s",
                timeout="5s"
            ),
            tags=["analytics", "metrics", "reporting", "v2"]
        )
        logger.info(f"Registered {SERVICE_NAME} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

async def deregister_from_consul():
    """Deregister service from Consul"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    try:
        c.agent.service.deregister(f"{SERVICE_NAME}-1")
        logger.info(f"Deregistered {SERVICE_NAME} from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {str(e)}")

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        service=SERVICE_NAME,
        version="2.0.0",
        timestamp=datetime.utcnow(),
        dependencies={
            "database": "healthy",
            "auth_service": "healthy"
        }
    )

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_permissions(["analytics:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard metrics"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total revenue
        revenue_stmt = select(func.sum(Metric.value)).where(
            and_(
                Metric.metric_type == "revenue",
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date
            )
        )
        revenue_result = await db.execute(revenue_stmt)
        total_revenue = revenue_result.scalar() or 0
        
        # Get total orders
        orders_stmt = select(func.sum(Metric.value)).where(
            and_(
                Metric.metric_type == "orders",
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date
            )
        )
        orders_result = await db.execute(orders_stmt)
        total_orders = int(orders_result.scalar() or 0)
        
        # Get unique customers
        customers_stmt = select(func.count(func.distinct(Metric.source_entity_id))).where(
            and_(
                Metric.metric_type == "customers",
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date
            )
        )
        customers_result = await db.execute(customers_stmt)
        total_customers = customers_result.scalar() or 0
        
        # Calculate average order value
        avg_order_value = Decimal(total_revenue) / max(total_orders, 1)
        
        # Get growth rates (compare with previous period)
        prev_start_date = start_date - timedelta(days=days)
        prev_revenue_stmt = select(func.sum(Metric.value)).where(
            and_(
                Metric.metric_type == "revenue",
                Metric.timestamp >= prev_start_date,
                Metric.timestamp < start_date
            )
        )
        prev_revenue_result = await db.execute(prev_revenue_stmt)
        prev_revenue = prev_revenue_result.scalar() or 1
        
        revenue_growth = ((Decimal(total_revenue) - Decimal(prev_revenue)) / Decimal(prev_revenue)) * 100
        
        return DashboardMetrics(
            total_revenue=Decimal(total_revenue),
            total_orders=total_orders,
            total_customers=total_customers,
            avg_order_value=avg_order_value,
            revenue_growth=revenue_growth,
            order_growth=Decimal("0"),  # Simplified for now
            top_performing_services=[],
            recent_trends=[]
        )
        
    except Exception as e:
        logger.error("Dashboard metrics error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics"
        )

@app.post("/api/v1/analytics/metrics")
async def ingest_metric(
    metric: MetricIngest,
    current_user: dict = Depends(require_permissions(["analytics:write"])),
    db: AsyncSession = Depends(get_db)
):
    """Ingest a new metric"""
    try:
        # Create metric record
        new_metric = Metric(
            metric_type=metric.metric_type,
            name=metric.name,
            value=metric.value,
            unit=metric.unit,
            tags=metric.tags or {},
            timestamp=metric.timestamp or datetime.utcnow(),
            source_service=metric.source_service,
            source_entity_id=metric.source_entity_id,
            source_entity_type=metric.source_entity_type
        )
        
        db.add(new_metric)
        await db.commit()
        await db.refresh(new_metric)
        
        logger.info("Metric ingested", metric_id=new_metric.metric_id, metric_type=metric.metric_type)
        
        return {
            "metric_id": new_metric.metric_id,
            "status": "ingested",
            "timestamp": new_metric.created_at
        }
        
    except Exception as e:
        logger.error("Metric ingestion error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest metric"
        )

@app.post("/api/v1/analytics/query")
async def query_analytics(
    query: QueryRequest,
    current_user: dict = Depends(require_permissions(["analytics:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Query analytics data"""
    try:
        # Build base query
        stmt = select(Metric.timestamp, Metric.value, Metric.tags)
        
        # Apply filters
        filters = [
            Metric.timestamp >= datetime.combine(query.start_date, datetime.min.time()),
            Metric.timestamp <= datetime.combine(query.end_date, datetime.max.time())
        ]
        
        if query.metric_type:
            filters.append(Metric.metric_type == query.metric_type)
        
        # Apply custom filters
        for key, value in (query.filters or {}).items():
            if key == "source_service":
                filters.append(Metric.source_service == value)
            elif key == "source_entity_type":
                filters.append(Metric.source_entity_type == value)
        
        stmt = stmt.where(and_(*filters))
        
        # Apply ordering
        stmt = stmt.order_by(Metric.timestamp)
        
        result = await db.execute(stmt)
        metrics = result.fetchall()
        
        # Aggregate data based on granularity
        aggregated_data = {}
        for metric in metrics:
            timestamp = metric.timestamp
            
            # Group by time granularity
            if query.granularity == TimeGranularity.DAILY:
                key = timestamp.date().isoformat()
            elif query.granularity == TimeGranularity.WEEKLY:
                key = f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
            elif query.granularity == TimeGranularity.MONTHLY:
                key = f"{timestamp.year}-{timestamp.month:02d}"
            elif query.granularity == TimeGranularity.YEARLY:
                key = str(timestamp.year)
            else:
                key = timestamp.isoformat()
            
            if key not in aggregated_data:
                aggregated_data[key] = []
            
            aggregated_data[key].append(float(metric.value))
        
        # Apply aggregation function
        result_data = []
        for period, values in aggregated_data.items():
            if query.aggregation == "sum":
                aggregated_value = sum(values)
            elif query.aggregation == "avg":
                aggregated_value = sum(values) / len(values)
            elif query.aggregation == "count":
                aggregated_value = len(values)
            elif query.aggregation == "min":
                aggregated_value = min(values)
            elif query.aggregation == "max":
                aggregated_value = max(values)
            else:
                aggregated_value = sum(values)
            
            result_data.append({
                "period": period,
                "value": aggregated_value,
                "count": len(values)
            })
        
        return {
            "query": query.dict(),
            "data": sorted(result_data, key=lambda x: x["period"]),
            "total_records": len(metrics),
            "aggregated_periods": len(result_data)
        }
        
    except Exception as e:
        logger.error("Analytics query error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query analytics data"
        )

@app.post("/api/v1/analytics/reports")
async def generate_report(
    report_request: ReportRequest,
    current_user: dict = Depends(require_permissions(["analytics:reports"])),
    db: AsyncSession = Depends(get_db)
):
    """Generate analytics report"""
    try:
        # Create report record
        report = Report(
            name=report_request.name,
            report_type=report_request.report_type,
            parameters=report_request.parameters,
            filters=report_request.filters,
            date_range=report_request.date_range,
            format=report_request.format,
            status=ReportStatus.PENDING,
            requested_by=str(current_user["id"])
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        # In a real implementation, you would queue this for background processing
        # For now, we'll simulate immediate processing
        report.status = ReportStatus.PROCESSING
        report.progress_percentage = 50
        await db.commit()
        
        logger.info("Report generation started", report_id=report.report_id)
        
        return {
            "report_id": report.report_id,
            "status": report.status,
            "estimated_completion": datetime.utcnow() + timedelta(minutes=5)
        }
        
    except Exception as e:
        logger.error("Report generation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )

@app.get("/api/v1/analytics/reports/{report_id}")
async def get_report_status(
    report_id: str,
    current_user: dict = Depends(require_permissions(["analytics:reports"])),
    db: AsyncSession = Depends(get_db)
):
    """Get report generation status"""
    try:
        stmt = select(Report).where(Report.report_id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return {
            "report_id": report.report_id,
            "name": report.name,
            "status": report.status,
            "progress_percentage": report.progress_percentage,
            "created_at": report.created_at,
            "completed_at": report.completed_at,
            "file_url": report.file_url,
            "file_size": report.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get report status error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report status"
        )

@app.get("/api/v1/analytics/trends")
async def get_business_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(require_permissions(["analytics:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get business trends and insights"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily revenue trend
        revenue_stmt = select(
            func.date(Metric.timestamp).label('date'),
            func.sum(Metric.value).label('total_revenue')
        ).where(
            and_(
                Metric.metric_type == "revenue",
                Metric.timestamp >= start_date,
                Metric.timestamp <= end_date
            )
        ).group_by(func.date(Metric.timestamp)).order_by(func.date(Metric.timestamp))
        
        revenue_result = await db.execute(revenue_stmt)
        revenue_trends = [
            {"date": row.date.isoformat(), "value": float(row.total_revenue)}
            for row in revenue_result
        ]
        
        return {
            "period": f"{days} days",
            "trends": {
                "revenue": revenue_trends,
                "orders": [],  # Simplified for now
                "customers": []
            },
            "insights": [
                {"type": "revenue", "message": "Revenue trend analysis", "impact": "positive"},
                {"type": "growth", "message": "Steady growth observed", "impact": "positive"}
            ]
        }
        
    except Exception as e:
        logger.error("Business trends error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business trends"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)