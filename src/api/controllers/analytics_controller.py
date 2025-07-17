from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session
from src.infrastructure.repositories.analytics_repository import AnalyticsRepository
from src.domain.services.analytics_service import AnalyticsService
from src.domain.entities.analytics import ReportType, MetricType
from src.infrastructure.logging.log_messages import LogCodes, QuantyLogger
from src.api.schemas.analytics_schemas import (
    DashboardCreate, WidgetCreate, WidgetUpdate, DashboardLayoutUpdate,
    ReportDefinitionCreate, ReportSchedule, ReportExecute, MetricDefinitionCreate,
    MetricValueRecord, KPICreate, KPIUpdate, KPITargetUpdate,
    DashboardResponse, WidgetResponse, ReportDefinitionResponse,
    ReportExecutionResponse, MetricDefinitionResponse, KPIResponse,
    MetricsSummaryResponse, KPIDashboardResponse, DashboardSummaryResponse,
    ReportStatusResponse
)

router = APIRouter()
logger = QuantyLogger()

@router.post("/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    request: DashboardCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear nuevo dashboard de analytics"""
    try:
        analytics_service = AnalyticsService()
        
        dashboard = analytics_service.create_dashboard(
            name=request.name,
            description=request.description,
            created_by=request.created_by
        )
        
        # Guardar en repositorio
        analytics_repo = AnalyticsRepository(session)
        saved_dashboard = await analytics_repo.create_dashboard(dashboard)
        
        logger.log_info(
            LogCodes.DASHBOARD_CREATED,
            f"Dashboard created: {dashboard.dashboard_id}",
            {"dashboard_id": dashboard.dashboard_id, "created_by": request.created_by}
        )
        
        return DashboardResponse(
            dashboard_id=saved_dashboard.dashboard_id,
            name=saved_dashboard.name,
            description=saved_dashboard.description,
            created_by=saved_dashboard.created_by,
            widgets_count=len(saved_dashboard.widgets),
            created_at=saved_dashboard.created_at,
            status=saved_dashboard.status.value
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.DASHBOARD_ERROR,
            f"Error creating dashboard: {str(e)}",
            {"error": str(e), "created_by": request.created_by}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener dashboard con datos actuales"""
    try:
        analytics_service = AnalyticsService()
        
        dashboard_summary = analytics_service.get_dashboard_summary(dashboard_id)
        
        return dashboard_summary
        
    except Exception as e:
        logger.log_error(
            LogCodes.DASHBOARD_ERROR,
            f"Error retrieving dashboard: {str(e)}",
            {"error": str(e), "dashboard_id": dashboard_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards/user/{user_id}", response_model=List[DashboardResponse])
async def get_user_dashboards(
    user_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener dashboards por usuario"""
    try:
        analytics_repo = AnalyticsRepository(session)
        dashboards = await analytics_repo.get_dashboards_by_user(user_id)
        
        return [
            DashboardResponse(
                dashboard_id=dashboard.dashboard_id,
                name=dashboard.name,
                description=dashboard.description,
                created_by=dashboard.created_by,
                widgets_count=len(dashboard.widgets),
                created_at=dashboard.created_at,
                status=dashboard.status.value
            )
            for dashboard in dashboards
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.DASHBOARD_ERROR,
            f"Error retrieving user dashboards: {str(e)}",
            {"error": str(e), "user_id": user_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/widgets", response_model=WidgetResponse)
async def create_widget(
    request: WidgetCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear nuevo widget"""
    try:
        analytics_service = AnalyticsService()
        
        widget = analytics_service.add_widget_to_dashboard(
            dashboard_id=request.dashboard_id,
            title=request.title,
            widget_type=request.widget_type,
            data_source=request.data_source,
            configuration=request.configuration
        )
        
        # Guardar en repositorio
        analytics_repo = AnalyticsRepository(session)
        saved_widget = await analytics_repo.create_widget(widget, request.dashboard_id)
        
        logger.log_info(
            LogCodes.WIDGET_CREATED,
            f"Widget created: {widget.widget_id}",
            {"widget_id": widget.widget_id, "dashboard_id": request.dashboard_id}
        )
        
        return WidgetResponse(
            widget_id=saved_widget.widget_id,
            title=saved_widget.title,
            widget_type=saved_widget.widget_type,
            data_source=saved_widget.data_source,
            is_enabled=saved_widget.is_enabled,
            position=saved_widget.position,
            created_at=saved_widget.created_at
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.WIDGET_ERROR,
            f"Error creating widget: {str(e)}",
            {"error": str(e), "dashboard_id": request.dashboard_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: str,
    request: WidgetUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Actualizar widget"""
    try:
        analytics_repo = AnalyticsRepository(session)
        
        # En implementación real, obtendría el widget existente y actualizaría
        # Por simplicidad, creamos un widget mock
        from src.domain.entities.analytics import AnalyticsWidget
        
        widget = AnalyticsWidget(
            widget_id=widget_id,
            title=request.title or "Updated Widget",
            widget_type="chart",
            data_source="mock"
        )
        
        if request.configuration:
            widget.update_configuration(request.configuration)
        
        if request.position:
            widget.position = request.position
        
        if request.is_enabled is not None:
            widget.is_enabled = request.is_enabled
        
        updated_widget = await analytics_repo.update_widget(widget)
        
        logger.log_info(
            LogCodes.WIDGET_UPDATED,
            f"Widget updated: {widget_id}",
            {"widget_id": widget_id}
        )
        
        return WidgetResponse(
            widget_id=updated_widget.widget_id,
            title=updated_widget.title,
            widget_type=updated_widget.widget_type,
            data_source=updated_widget.data_source,
            is_enabled=updated_widget.is_enabled,
            position=updated_widget.position,
            created_at=updated_widget.created_at
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.WIDGET_ERROR,
            f"Error updating widget: {str(e)}",
            {"error": str(e), "widget_id": widget_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report-definitions", response_model=ReportDefinitionResponse)
async def create_report_definition(
    request: ReportDefinitionCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear definición de reporte"""
    try:
        analytics_service = AnalyticsService()
        
        report_def = analytics_service.create_report_definition(
            name=request.name,
            report_type=ReportType(request.report_type),
            description=request.description,
            data_sources=request.data_sources,
            created_by="system",  # En implementación real vendría del contexto
            template_path=request.template_path
        )
        
        # Guardar en repositorio
        analytics_repo = AnalyticsRepository(session)
        saved_report_def = await analytics_repo.create_report_definition(report_def)
        
        logger.log_info(
            LogCodes.REPORT_CREATED,
            f"Report definition created: {report_def.report_id}",
            {"report_id": report_def.report_id, "type": request.report_type}
        )
        
        return ReportDefinitionResponse(
            report_id=saved_report_def.report_id,
            name=saved_report_def.name,
            report_type=saved_report_def.report_type.value,
            description=saved_report_def.description,
            created_by=saved_report_def.created_by,
            is_active=saved_report_def.is_active,
            data_sources=saved_report_def.data_sources,
            created_at=saved_report_def.created_at
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.REPORT_ERROR,
            f"Error creating report definition: {str(e)}",
            {"error": str(e), "name": request.name}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report-definitions/{report_id}/schedule")
async def schedule_report(
    report_id: str,
    request: ReportSchedule,
    session: AsyncSession = Depends(get_session)
):
    """Programar ejecución automática de reporte"""
    try:
        analytics_service = AnalyticsService()
        
        schedule = analytics_service.schedule_report(
            report_id=report_id,
            frequency=request.frequency,
            time_of_day=request.time_of_day,
            day_of_week=request.day_of_week,
            day_of_month=request.day_of_month
        )
        
        logger.log_info(
            LogCodes.REPORT_SCHEDULED,
            f"Report scheduled: {report_id}",
            {"report_id": report_id, "frequency": request.frequency}
        )
        
        return {
            "success": True,
            "next_run_time": schedule.next_run_time,
            "message": "Report scheduled successfully"
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.REPORT_ERROR,
            f"Error scheduling report: {str(e)}",
            {"error": str(e), "report_id": report_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/execute", response_model=ReportExecutionResponse)
async def execute_report(
    request: ReportExecute,
    session: AsyncSession = Depends(get_session)
):
    """Ejecutar reporte"""
    try:
        analytics_service = AnalyticsService()
        
        execution = analytics_service.execute_report(
            report_id=request.report_id,
            requested_by="system",  # En implementación real vendría del contexto
            parameters=request.parameters,
            output_format=request.output_format
        )
        
        # Guardar en repositorio
        analytics_repo = AnalyticsRepository(session)
        saved_execution = await analytics_repo.create_report_execution(execution)
        
        logger.log_info(
            LogCodes.REPORT_EXECUTED,
            f"Report executed: {execution.execution_id}",
            {"execution_id": execution.execution_id, "report_id": request.report_id}
        )
        
        return ReportExecutionResponse(
            execution_id=saved_execution.execution_id,
            report_id=request.report_id,
            status=saved_execution.status.value,
            requested_by=saved_execution.requested_by,
            created_at=saved_execution.created_at,
            file_path=saved_execution.file_path,
            execution_time_seconds=saved_execution.execution_time_seconds
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.REPORT_ERROR,
            f"Error executing report: {str(e)}",
            {"error": str(e), "report_id": request.report_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics", response_model=MetricDefinitionResponse)
async def register_metric(
    request: MetricDefinitionCreate,
    session: AsyncSession = Depends(get_session)
):
    """Registrar nueva métrica"""
    try:
        analytics_service = AnalyticsService()
        
        metric = analytics_service.register_metric(
            name=request.name,
            description=request.description,
            metric_type=MetricType(request.metric_type),
            unit=request.unit,
            tags=request.tags,
            retention_days=request.retention_days
        )
        
        # Guardar en repositorio
        analytics_repo = AnalyticsRepository(session)
        saved_metric = await analytics_repo.create_metric_definition(metric)
        
        logger.log_info(
            LogCodes.METRIC_REGISTERED,
            f"Metric registered: {metric.metric_id}",
            {"metric_id": metric.metric_id, "name": request.name}
        )
        
        return MetricDefinitionResponse(
            metric_id=saved_metric.metric_id,
            name=saved_metric.name,
            description=saved_metric.description,
            metric_type=saved_metric.metric_type.value,
            unit=saved_metric.unit,
            retention_days=saved_metric.retention_days
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.METRIC_ERROR,
            f"Error registering metric: {str(e)}",
            {"error": str(e), "name": request.name}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/values")
async def record_metric_value(
    request: MetricValueRecord,
    session: AsyncSession = Depends(get_session)
):
    """Registrar valor de métrica"""
    try:
        analytics_service = AnalyticsService()
        
        analytics_service.record_metric_value(
            metric_name=request.metric_name,
            value=request.value,
            tags=request.tags,
            timestamp=request.timestamp
        )
        
        logger.log_info(
            LogCodes.METRIC_VALUE_RECORDED,
            f"Metric value recorded: {request.metric_name}",
            {"metric_name": request.metric_name, "value": request.value}
        )
        
        return {"success": True, "message": "Metric value recorded successfully"}
        
    except Exception as e:
        logger.log_error(
            LogCodes.METRIC_ERROR,
            f"Error recording metric value: {str(e)}",
            {"error": str(e), "metric_name": request.metric_name}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    metric_names: Optional[List[str]] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Obtener resumen de métricas"""
    try:
        analytics_service = AnalyticsService()
        
        summary = analytics_service.get_metrics_summary(
            start_time=start_time,
            end_time=end_time,
            metric_names=metric_names
        )
        
        return MetricsSummaryResponse(**summary)
        
    except Exception as e:
        logger.log_error(
            LogCodes.METRIC_ERROR,
            f"Error retrieving metrics summary: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kpis", response_model=KPIResponse)
async def create_kpi(
    request: KPICreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear nuevo KPI"""
    try:
        analytics_service = AnalyticsService()
        
        kpi = analytics_service.create_kpi(
            name=request.name,
            description=request.description,
            target_value=request.target_value,
            unit=request.unit
        )
        
        # Guardar en repositorio
        analytics_repo = AnalyticsRepository(session)
        saved_kpi = await analytics_repo.create_kpi(kpi)
        
        logger.log_info(
            LogCodes.KPI_CREATED,
            f"KPI created: {kpi.kpi_id}",
            {"kpi_id": kpi.kpi_id, "name": request.name}
        )
        
        return KPIResponse(
            kpi_id=saved_kpi.kpi_id,
            name=saved_kpi.name,
            description=saved_kpi.description,
            target_value=saved_kpi.target_value,
            current_value=saved_kpi.current_value,
            unit=saved_kpi.unit,
            status=saved_kpi.status,
            trend=saved_kpi.trend,
            performance_percentage=saved_kpi.get_performance_percentage()
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.KPI_ERROR,
            f"Error creating KPI: {str(e)}",
            {"error": str(e), "name": request.name}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/kpis/{kpi_id}/value", response_model=KPIResponse)
async def update_kpi_value(
    kpi_id: str,
    request: KPIUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Actualizar valor de KPI"""
    try:
        analytics_service = AnalyticsService()
        
        kpi = analytics_service.update_kpi_value(
            kpi_id=kpi_id,
            new_value=request.new_value
        )
        
        # Actualizar en repositorio
        analytics_repo = AnalyticsRepository(session)
        updated_kpi = await analytics_repo.update_kpi(kpi)
        
        logger.log_info(
            LogCodes.KPI_UPDATED,
            f"KPI value updated: {kpi_id}",
            {"kpi_id": kpi_id, "new_value": request.new_value}
        )
        
        return KPIResponse(
            kpi_id=updated_kpi.kpi_id,
            name=updated_kpi.name,
            description=updated_kpi.description,
            target_value=updated_kpi.target_value,
            current_value=updated_kpi.current_value,
            unit=updated_kpi.unit,
            status=updated_kpi.status,
            trend=updated_kpi.trend,
            performance_percentage=updated_kpi.get_performance_percentage()
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.KPI_ERROR,
            f"Error updating KPI value: {str(e)}",
            {"error": str(e), "kpi_id": kpi_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kpis/dashboard", response_model=KPIDashboardResponse)
async def get_kpis_dashboard(
    session: AsyncSession = Depends(get_session)
):
    """Obtener dashboard de KPIs"""
    try:
        analytics_service = AnalyticsService()
        
        dashboard = analytics_service.get_kpis_dashboard()
        
        return KPIDashboardResponse(**dashboard)
        
    except Exception as e:
        logger.log_error(
            LogCodes.KPI_ERROR,
            f"Error retrieving KPIs dashboard: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/status")
async def get_reports_status(
    session: AsyncSession = Depends(get_session)
):
    """Obtener estado de todos los reportes"""
    try:
        analytics_service = AnalyticsService()
        
        status = analytics_service.get_reports_status()
        
        return status
        
    except Exception as e:
        logger.log_error(
            LogCodes.REPORT_ERROR,
            f"Error retrieving reports status: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards/public", response_model=List[DashboardResponse])
async def get_public_dashboards(
    session: AsyncSession = Depends(get_session)
):
    """Obtener dashboards públicos"""
    try:
        analytics_repo = AnalyticsRepository(session)
        dashboards = await analytics_repo.get_public_dashboards()
        
        return [
            DashboardResponse(
                dashboard_id=dashboard.dashboard_id,
                name=dashboard.name,
                description=dashboard.description,
                created_by=dashboard.created_by,
                widgets_count=len(dashboard.widgets),
                created_at=dashboard.created_at,
                status=dashboard.status.value
            )
            for dashboard in dashboards
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.DASHBOARD_ERROR,
            f"Error retrieving public dashboards: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Eliminar dashboard"""
    try:
        analytics_repo = AnalyticsRepository(session)
        success = await analytics_repo.delete_dashboard(dashboard_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        logger.log_info(
            LogCodes.DASHBOARD_DELETED,
            f"Dashboard deleted: {dashboard_id}",
            {"dashboard_id": dashboard_id}
        )
        
        return {"success": True, "message": "Dashboard deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.DASHBOARD_ERROR,
            f"Error deleting dashboard: {str(e)}",
            {"error": str(e), "dashboard_id": dashboard_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/widgets/{widget_id}")
async def delete_widget(
    widget_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Eliminar widget"""
    try:
        analytics_repo = AnalyticsRepository(session)
        success = await analytics_repo.delete_widget(widget_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        logger.log_info(
            LogCodes.WIDGET_DELETED,
            f"Widget deleted: {widget_id}",
            {"widget_id": widget_id}
        )
        
        return {"success": True, "message": "Widget deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.WIDGET_ERROR,
            f"Error deleting widget: {str(e)}",
            {"error": str(e), "widget_id": widget_id}
        )
        raise HTTPException(status_code=500, detail=str(e))