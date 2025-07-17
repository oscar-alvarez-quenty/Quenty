from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from src.domain.entities.analytics import (
    AnalyticsDashboard, AnalyticsWidget, ReportDefinition, 
    ReportExecution, MetricDefinition, MetricValue, PerformanceKPI
)
from src.infrastructure.models.analytics_models import (
    AnalyticsDashboardModel, AnalyticsWidgetModel, ReportDefinitionModel,
    ReportExecutionModel, MetricDefinitionModel, MetricValueModel, 
    PerformanceKPIModel
)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Dashboard methods
    async def create_dashboard(self, dashboard: AnalyticsDashboard) -> AnalyticsDashboard:
        """Crear nuevo dashboard"""
        dashboard_model = AnalyticsDashboardModel(
            dashboard_id=dashboard.dashboard_id,
            name=dashboard.name,
            description=dashboard.description,
            created_by=dashboard.created_by,
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
            is_public=dashboard.is_public,
            permissions=str(dashboard.permissions),
            refresh_interval_minutes=dashboard.refresh_interval_minutes,
            status=dashboard.status.value
        )
        
        self.session.add(dashboard_model)
        await self.session.commit()
        await self.session.refresh(dashboard_model)
        
        return dashboard

    async def get_dashboard(self, dashboard_id: str) -> Optional[AnalyticsDashboard]:
        """Obtener dashboard por ID"""
        stmt = (
            select(AnalyticsDashboardModel)
            .options(selectinload(AnalyticsDashboardModel.widgets))
            .where(AnalyticsDashboardModel.dashboard_id == dashboard_id)
        )
        
        result = await self.session.execute(stmt)
        dashboard_model = result.scalar_one_or_none()
        
        if dashboard_model:
            return self._dashboard_model_to_entity(dashboard_model)
        return None

    async def update_dashboard(self, dashboard: AnalyticsDashboard) -> AnalyticsDashboard:
        """Actualizar dashboard"""
        stmt = (
            update(AnalyticsDashboardModel)
            .where(AnalyticsDashboardModel.dashboard_id == dashboard.dashboard_id)
            .values(
                name=dashboard.name,
                description=dashboard.description,
                updated_at=dashboard.updated_at,
                is_public=dashboard.is_public,
                permissions=str(dashboard.permissions),
                refresh_interval_minutes=dashboard.refresh_interval_minutes,
                status=dashboard.status.value
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return dashboard

    async def get_dashboards_by_user(self, user_id: str) -> List[AnalyticsDashboard]:
        """Obtener dashboards por usuario"""
        stmt = (
            select(AnalyticsDashboardModel)
            .options(selectinload(AnalyticsDashboardModel.widgets))
            .where(AnalyticsDashboardModel.created_by == user_id)
            .order_by(AnalyticsDashboardModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        dashboard_models = result.scalars().all()
        
        return [self._dashboard_model_to_entity(model) for model in dashboard_models]

    async def get_public_dashboards(self) -> List[AnalyticsDashboard]:
        """Obtener dashboards públicos"""
        stmt = (
            select(AnalyticsDashboardModel)
            .options(selectinload(AnalyticsDashboardModel.widgets))
            .where(AnalyticsDashboardModel.is_public == True)
            .order_by(AnalyticsDashboardModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        dashboard_models = result.scalars().all()
        
        return [self._dashboard_model_to_entity(model) for model in dashboard_models]

    # Widget methods
    async def create_widget(self, widget: AnalyticsWidget, dashboard_id: str) -> AnalyticsWidget:
        """Crear nuevo widget"""
        widget_model = AnalyticsWidgetModel(
            widget_id=widget.widget_id,
            dashboard_id=dashboard_id,
            title=widget.title,
            widget_type=widget.widget_type,
            data_source=widget.data_source,
            created_at=widget.created_at,
            updated_at=widget.updated_at,
            configuration=str(widget.configuration),
            position_x=widget.position["x"],
            position_y=widget.position["y"],
            position_width=widget.position["width"],
            position_height=widget.position["height"],
            is_enabled=widget.is_enabled,
            refresh_interval_seconds=widget.refresh_interval_seconds
        )
        
        self.session.add(widget_model)
        await self.session.commit()
        await self.session.refresh(widget_model)
        
        return widget

    async def update_widget(self, widget: AnalyticsWidget) -> AnalyticsWidget:
        """Actualizar widget"""
        stmt = (
            update(AnalyticsWidgetModel)
            .where(AnalyticsWidgetModel.widget_id == widget.widget_id)
            .values(
                title=widget.title,
                updated_at=widget.updated_at,
                configuration=str(widget.configuration),
                position_x=widget.position["x"],
                position_y=widget.position["y"],
                position_width=widget.position["width"],
                position_height=widget.position["height"],
                is_enabled=widget.is_enabled,
                refresh_interval_seconds=widget.refresh_interval_seconds
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return widget

    async def delete_widget(self, widget_id: str) -> bool:
        """Eliminar widget"""
        stmt = delete(AnalyticsWidgetModel).where(AnalyticsWidgetModel.widget_id == widget_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    # Report Definition methods
    async def create_report_definition(self, report_def: ReportDefinition) -> ReportDefinition:
        """Crear definición de reporte"""
        report_model = ReportDefinitionModel(
            report_id=report_def.report_id,
            name=report_def.name,
            report_type=report_def.report_type.value,
            description=report_def.description,
            created_by=report_def.created_by,
            created_at=report_def.created_at,
            updated_at=report_def.updated_at,
            parameters=str(report_def.parameters),
            filters=str(report_def.filters),
            data_sources=",".join(report_def.data_sources),
            output_formats=",".join(report_def.output_formats),
            is_active=report_def.is_active,
            template_path=report_def.template_path
        )
        
        self.session.add(report_model)
        await self.session.commit()
        await self.session.refresh(report_model)
        
        return report_def

    async def get_report_definition(self, report_id: str) -> Optional[ReportDefinition]:
        """Obtener definición de reporte por ID"""
        stmt = (
            select(ReportDefinitionModel)
            .options(selectinload(ReportDefinitionModel.executions))
            .where(ReportDefinitionModel.report_id == report_id)
        )
        
        result = await self.session.execute(stmt)
        report_model = result.scalar_one_or_none()
        
        if report_model:
            return self._report_definition_model_to_entity(report_model)
        return None

    async def get_active_report_definitions(self) -> List[ReportDefinition]:
        """Obtener definiciones de reportes activos"""
        stmt = (
            select(ReportDefinitionModel)
            .where(ReportDefinitionModel.is_active == True)
            .order_by(ReportDefinitionModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        report_models = result.scalars().all()
        
        return [self._report_definition_model_to_entity(model) for model in report_models]

    # Report Execution methods
    async def create_report_execution(self, execution: ReportExecution) -> ReportExecution:
        """Crear ejecución de reporte"""
        execution_model = ReportExecutionModel(
            execution_id=execution.execution_id,
            report_id=execution.report_definition.report_id,
            requested_by=execution.requested_by,
            parameters=str(execution.parameters),
            status=execution.status.value,
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            file_path=execution.file_path,
            file_size_bytes=execution.file_size_bytes,
            output_format=execution.output_format,
            error_message=execution.error_message,
            execution_time_seconds=execution.execution_time_seconds
        )
        
        self.session.add(execution_model)
        await self.session.commit()
        await self.session.refresh(execution_model)
        
        return execution

    async def update_report_execution(self, execution: ReportExecution) -> ReportExecution:
        """Actualizar ejecución de reporte"""
        stmt = (
            update(ReportExecutionModel)
            .where(ReportExecutionModel.execution_id == execution.execution_id)
            .values(
                status=execution.status.value,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                file_path=execution.file_path,
                file_size_bytes=execution.file_size_bytes,
                error_message=execution.error_message,
                execution_time_seconds=execution.execution_time_seconds
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return execution

    async def get_report_executions_by_user(
        self, 
        user_id: str,
        limit: int = 50
    ) -> List[ReportExecution]:
        """Obtener ejecuciones de reportes por usuario"""
        stmt = (
            select(ReportExecutionModel)
            .where(ReportExecutionModel.requested_by == user_id)
            .order_by(ReportExecutionModel.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        execution_models = result.scalars().all()
        
        return [self._report_execution_model_to_entity(model) for model in execution_models]

    # Metric methods
    async def create_metric_definition(self, metric: MetricDefinition) -> MetricDefinition:
        """Crear definición de métrica"""
        metric_model = MetricDefinitionModel(
            metric_id=metric.metric_id,
            name=metric.name,
            description=metric.description,
            metric_type=metric.metric_type.value,
            unit=metric.unit,
            tags=str(metric.tags),
            aggregation_period=metric.aggregation_period,
            retention_days=metric.retention_days
        )
        
        self.session.add(metric_model)
        await self.session.commit()
        await self.session.refresh(metric_model)
        
        return metric

    async def get_metric_definition(self, metric_id: str) -> Optional[MetricDefinition]:
        """Obtener definición de métrica por ID"""
        stmt = select(MetricDefinitionModel).where(MetricDefinitionModel.metric_id == metric_id)
        result = await self.session.execute(stmt)
        metric_model = result.scalar_one_or_none()
        
        if metric_model:
            return self._metric_definition_model_to_entity(metric_model)
        return None

    async def get_all_metric_definitions(self) -> List[MetricDefinition]:
        """Obtener todas las definiciones de métricas"""
        stmt = select(MetricDefinitionModel).order_by(MetricDefinitionModel.name)
        result = await self.session.execute(stmt)
        metric_models = result.scalars().all()
        
        return [self._metric_definition_model_to_entity(model) for model in metric_models]

    async def create_metric_value(self, metric_value: MetricValue) -> MetricValue:
        """Crear valor de métrica"""
        value_model = MetricValueModel(
            metric_id=metric_value.metric_id,
            timestamp=metric_value.timestamp,
            value=float(metric_value.value),
            tags=str(metric_value.tags) if metric_value.tags else None,
            dimensions=str(metric_value.dimensions) if metric_value.dimensions else None
        )
        
        self.session.add(value_model)
        await self.session.commit()
        await self.session.refresh(value_model)
        
        return metric_value

    async def get_metric_values(
        self,
        metric_id: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> List[MetricValue]:
        """Obtener valores de métrica en rango de tiempo"""
        conditions = [
            MetricValueModel.metric_id == metric_id,
            MetricValueModel.timestamp >= start_time,
            MetricValueModel.timestamp <= end_time
        ]
        
        stmt = (
            select(MetricValueModel)
            .where(and_(*conditions))
            .order_by(MetricValueModel.timestamp)
        )
        
        result = await self.session.execute(stmt)
        value_models = result.scalars().all()
        
        metric_values = [self._metric_value_model_to_entity(model) for model in value_models]
        
        # Filtrar por tags si se especifican
        if tags:
            filtered_values = []
            for value in metric_values:
                if value.tags and all(value.tags.get(k) == v for k, v in tags.items()):
                    filtered_values.append(value)
            return filtered_values
        
        return metric_values

    # KPI methods
    async def create_kpi(self, kpi: PerformanceKPI) -> PerformanceKPI:
        """Crear KPI"""
        kpi_model = PerformanceKPIModel(
            kpi_id=kpi.kpi_id,
            name=kpi.name,
            description=kpi.description,
            target_value=kpi.target_value,
            unit=kpi.unit,
            current_value=kpi.current_value,
            last_updated=kpi.last_updated,
            trend=kpi.trend,
            status=kpi.status
        )
        
        self.session.add(kpi_model)
        await self.session.commit()
        await self.session.refresh(kpi_model)
        
        return kpi

    async def update_kpi(self, kpi: PerformanceKPI) -> PerformanceKPI:
        """Actualizar KPI"""
        stmt = (
            update(PerformanceKPIModel)
            .where(PerformanceKPIModel.kpi_id == kpi.kpi_id)
            .values(
                current_value=kpi.current_value,
                last_updated=kpi.last_updated,
                trend=kpi.trend,
                status=kpi.status
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return kpi

    async def get_all_kpis(self) -> List[PerformanceKPI]:
        """Obtener todos los KPIs"""
        stmt = select(PerformanceKPIModel).order_by(PerformanceKPIModel.name)
        result = await self.session.execute(stmt)
        kpi_models = result.scalars().all()
        
        return [self._kpi_model_to_entity(model) for model in kpi_models]

    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Eliminar dashboard"""
        stmt = delete(AnalyticsDashboardModel).where(AnalyticsDashboardModel.dashboard_id == dashboard_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    # Conversion methods
    def _dashboard_model_to_entity(self, model: AnalyticsDashboardModel) -> AnalyticsDashboard:
        """Convertir modelo de dashboard a entidad"""
        from src.domain.entities.analytics import AnalyticsStatus
        
        dashboard = AnalyticsDashboard(
            dashboard_id=model.dashboard_id,
            name=model.name,
            description=model.description,
            created_by=model.created_by
        )
        
        # Asignar propiedades
        dashboard.created_at = model.created_at
        dashboard.updated_at = model.updated_at
        dashboard.is_public = model.is_public
        dashboard.refresh_interval_minutes = model.refresh_interval_minutes
        dashboard.status = AnalyticsStatus(model.status)
        
        # Parsear permisos
        if model.permissions:
            import json
            try:
                dashboard.permissions = json.loads(model.permissions)
            except:
                dashboard.permissions = {}
        
        # Cargar widgets
        if hasattr(model, 'widgets') and model.widgets:
            dashboard.widgets = [self._widget_model_to_entity(widget) for widget in model.widgets]
        
        return dashboard

    def _widget_model_to_entity(self, model: AnalyticsWidgetModel) -> AnalyticsWidget:
        """Convertir modelo de widget a entidad"""
        widget = AnalyticsWidget(
            widget_id=model.widget_id,
            title=model.title,
            widget_type=model.widget_type,
            data_source=model.data_source
        )
        
        # Asignar propiedades
        widget.created_at = model.created_at
        widget.updated_at = model.updated_at
        widget.is_enabled = model.is_enabled
        widget.refresh_interval_seconds = model.refresh_interval_seconds
        
        # Configurar posición
        widget.position = {
            "x": model.position_x,
            "y": model.position_y,
            "width": model.position_width,
            "height": model.position_height
        }
        
        # Parsear configuración
        if model.configuration:
            import json
            try:
                widget.configuration = json.loads(model.configuration)
            except:
                widget.configuration = {}
        
        return widget

    def _report_definition_model_to_entity(self, model: ReportDefinitionModel) -> ReportDefinition:
        """Convertir modelo de definición de reporte a entidad"""
        from src.domain.entities.analytics import ReportType
        
        report_def = ReportDefinition(
            report_id=model.report_id,
            name=model.name,
            report_type=ReportType(model.report_type),
            description=model.description,
            created_by=model.created_by
        )
        
        # Asignar propiedades
        report_def.created_at = model.created_at
        report_def.updated_at = model.updated_at
        report_def.is_active = model.is_active
        report_def.template_path = model.template_path
        
        if model.data_sources:
            report_def.data_sources = model.data_sources.split(',')
        
        if model.output_formats:
            report_def.output_formats = model.output_formats.split(',')
        
        # Parsear parámetros y filtros
        if model.parameters:
            import json
            try:
                report_def.parameters = json.loads(model.parameters)
            except:
                report_def.parameters = {}
        
        if model.filters:
            import json
            try:
                report_def.filters = json.loads(model.filters)
            except:
                report_def.filters = {}
        
        return report_def

    def _report_execution_model_to_entity(self, model: ReportExecutionModel) -> ReportExecution:
        """Convertir modelo de ejecución de reporte a entidad"""
        from src.domain.entities.analytics import ReportStatus
        
        # Necesitamos crear un ReportDefinition mock para la ejecución
        mock_report_def = ReportDefinition(
            report_id=model.report_id,
            name="Report",
            report_type="sales",  # Valor por defecto
            description="",
            created_by=""
        )
        
        execution = ReportExecution(
            execution_id=model.execution_id,
            report_definition=mock_report_def,
            requested_by=model.requested_by
        )
        
        # Asignar propiedades
        execution.status = ReportStatus(model.status)
        execution.created_at = model.created_at
        execution.started_at = model.started_at
        execution.completed_at = model.completed_at
        execution.file_path = model.file_path
        execution.file_size_bytes = model.file_size_bytes
        execution.output_format = model.output_format
        execution.error_message = model.error_message
        execution.execution_time_seconds = model.execution_time_seconds
        
        # Parsear parámetros
        if model.parameters:
            import json
            try:
                execution.parameters = json.loads(model.parameters)
            except:
                execution.parameters = {}
        
        return execution

    def _metric_definition_model_to_entity(self, model: MetricDefinitionModel) -> MetricDefinition:
        """Convertir modelo de definición de métrica a entidad"""
        from src.domain.entities.analytics import MetricType
        
        metric = MetricDefinition(
            metric_id=model.metric_id,
            name=model.name,
            description=model.description,
            metric_type=MetricType(model.metric_type),
            unit=model.unit,
            tags={},
            aggregation_period=model.aggregation_period,
            retention_days=model.retention_days
        )
        
        # Parsear tags
        if model.tags:
            import json
            try:
                metric.tags = json.loads(model.tags)
            except:
                metric.tags = {}
        
        return metric

    def _metric_value_model_to_entity(self, model: MetricValueModel) -> MetricValue:
        """Convertir modelo de valor de métrica a entidad"""
        metric_value = MetricValue(
            metric_id=model.metric_id,
            timestamp=model.timestamp,
            value=model.value
        )
        
        # Parsear tags y dimensiones
        if model.tags:
            import json
            try:
                metric_value.tags = json.loads(model.tags)
            except:
                metric_value.tags = {}
        
        if model.dimensions:
            import json
            try:
                metric_value.dimensions = json.loads(model.dimensions)
            except:
                metric_value.dimensions = {}
        
        return metric_value

    def _kpi_model_to_entity(self, model: PerformanceKPIModel) -> PerformanceKPI:
        """Convertir modelo de KPI a entidad"""
        kpi = PerformanceKPI(
            kpi_id=model.kpi_id,
            name=model.name,
            description=model.description,
            target_value=model.target_value,
            unit=model.unit
        )
        
        # Asignar propiedades
        kpi.current_value = model.current_value
        kpi.last_updated = model.last_updated
        kpi.trend = model.trend
        kpi.status = model.status
        
        return kpi