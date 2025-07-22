from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict
import consul
from datetime import datetime, date, timedelta
from enum import Enum

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "analytics-service"
    database_url: str = "postgresql+asyncpg://analytics:analytics_pass@analytics-db:5432/analytics_db"
    redis_url: str = "redis://redis:6379/6"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Analytics Service",
    description="Microservice for business analytics and reporting",
    version="2.0.0"
)

# Enums
class MetricType(str, Enum):
    REVENUE = "revenue"
    ORDERS = "orders"
    CUSTOMERS = "customers"
    PACKAGES = "packages"
    DELIVERY_TIME = "delivery_time"
    SATISFACTION = "satisfaction"

class TimeGranularity(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class ReportType(str, Enum):
    PERFORMANCE = "performance"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"

# Pydantic models
class MetricData(BaseModel):
    metric_name: str
    value: float
    timestamp: datetime
    dimensions: Dict[str, str] = Field(default_factory=dict)

class DashboardMetric(BaseModel):
    metric_type: MetricType
    current_value: float
    previous_value: float
    change_percentage: float
    trend: str  # "up", "down", "stable"
    period: str

class AnalyticsQuery(BaseModel):
    metrics: List[MetricType]
    start_date: date
    end_date: date
    granularity: TimeGranularity
    dimensions: Optional[List[str]] = None
    filters: Optional[Dict[str, str]] = None

class ReportRequest(BaseModel):
    report_type: ReportType
    start_date: date
    end_date: date
    include_comparisons: bool = True
    export_format: str = "json"  # json, csv, pdf

class AnalyticsResponse(BaseModel):
    query_id: str
    metrics: List[Dict]
    time_range: Dict[str, str]
    granularity: str
    generated_at: datetime

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_metrics():
    # Mock implementation
    return {
        "metrics": [
            DashboardMetric(
                metric_type=MetricType.REVENUE,
                current_value=1250000.0,
                previous_value=1100000.0,
                change_percentage=13.6,
                trend="up",
                period="last_30_days"
            ).dict(),
            DashboardMetric(
                metric_type=MetricType.ORDERS,
                current_value=15420,
                previous_value=14200,
                change_percentage=8.6,
                trend="up",
                period="last_30_days"
            ).dict(),
            DashboardMetric(
                metric_type=MetricType.CUSTOMERS,
                current_value=8750,
                previous_value=8200,
                change_percentage=6.7,
                trend="up",
                period="last_30_days"
            ).dict(),
            DashboardMetric(
                metric_type=MetricType.DELIVERY_TIME,
                current_value=2.5,
                previous_value=3.1,
                change_percentage=-19.4,
                trend="down",
                period="last_30_days"
            ).dict()
        ],
        "last_updated": datetime.utcnow()
    }

@app.post("/api/v1/analytics/query", response_model=AnalyticsResponse)
async def query_analytics(query: AnalyticsQuery):
    # Mock implementation
    mock_data = []
    for metric in query.metrics:
        mock_data.append({
            "metric": metric,
            "data_points": [
                {
                    "timestamp": (query.start_date + timedelta(days=i)).isoformat(),
                    "value": 1000 + (i * 50),
                    "dimensions": query.dimensions or {}
                }
                for i in range(7)
            ]
        })
    
    return AnalyticsResponse(
        query_id="QUERY-001",
        metrics=mock_data,
        time_range={
            "start": query.start_date.isoformat(),
            "end": query.end_date.isoformat()
        },
        granularity=query.granularity,
        generated_at=datetime.utcnow()
    )

@app.get("/api/v1/analytics/metrics/{metric_type}")
async def get_metric_details(
    metric_type: MetricType,
    start_date: date = Query(...),
    end_date: date = Query(...),
    granularity: TimeGranularity = TimeGranularity.DAILY
):
    # Mock implementation
    return {
        "metric": metric_type,
        "summary": {
            "total": 125000.0,
            "average": 4166.67,
            "min": 2500.0,
            "max": 7500.0
        },
        "data_points": [
            {
                "date": (start_date + timedelta(days=i)).isoformat(),
                "value": 3000 + (i * 500)
            }
            for i in range(7)
        ]
    }

@app.post("/api/v1/analytics/reports")
async def generate_report(report_request: ReportRequest):
    # Mock implementation
    return {
        "report_id": "RPT-001",
        "report_type": report_request.report_type,
        "status": "generating",
        "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        "download_url": f"/api/v1/analytics/reports/RPT-001/download"
    }

@app.get("/api/v1/analytics/reports/{report_id}")
async def get_report_status(report_id: str):
    # Mock implementation
    return {
        "report_id": report_id,
        "status": "completed",
        "generated_at": datetime.utcnow(),
        "size_bytes": 245678,
        "download_url": f"/api/v1/analytics/reports/{report_id}/download"
    }

@app.get("/api/v1/analytics/trends")
async def get_business_trends():
    # Mock implementation
    return {
        "trends": [
            {
                "trend_name": "Peak Order Hours",
                "description": "Most orders occur between 2-4 PM",
                "impact": "high",
                "recommendation": "Increase delivery capacity during these hours"
            },
            {
                "trend_name": "Weekend Surge",
                "description": "30% increase in orders on weekends",
                "impact": "medium",
                "recommendation": "Schedule more drivers for weekend shifts"
            },
            {
                "trend_name": "Customer Retention",
                "description": "85% of customers place repeat orders within 30 days",
                "impact": "high",
                "recommendation": "Focus on first-time customer experience"
            }
        ],
        "generated_at": datetime.utcnow()
    }

@app.post("/api/v1/analytics/metrics")
async def ingest_metric(metric: MetricData):
    # Mock implementation - in real scenario, this would store metrics
    return {
        "status": "accepted",
        "metric_id": "MET-001",
        "timestamp": datetime.utcnow()
    }

@app.get("/api/v1/analytics/alerts")
async def get_analytics_alerts():
    # Mock implementation
    return {
        "alerts": [
            {
                "alert_id": "ALERT-001",
                "type": "threshold_breach",
                "metric": "delivery_time",
                "message": "Average delivery time exceeded 3 hours",
                "severity": "high",
                "triggered_at": datetime.utcnow()
            },
            {
                "alert_id": "ALERT-002",
                "type": "anomaly",
                "metric": "order_volume",
                "message": "Unusual spike in order volume detected",
                "severity": "medium",
                "triggered_at": datetime.utcnow()
            }
        ]
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="analytics-service",
            port=8006,
            check=consul.Check.http(
                url="http://analytics-service:8006/health",
                interval="10s",
                timeout="5s"
            )
        )
        logger.info(f"Registered {settings.service_name} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

@app.on_event("startup")
async def startup_event():
    await register_with_consul()
    logger.info(f"{settings.service_name} started")

@app.on_event("shutdown")
async def shutdown_event():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.deregister(f"{settings.service_name}-1")
        logger.info(f"Deregistered {settings.service_name} from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)