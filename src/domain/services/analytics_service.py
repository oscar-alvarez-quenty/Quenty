from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import json

from src.domain.entities.analytics import (
    AnalyticsDashboard, AnalyticsWidget, ReportDefinition, ReportExecution,
    ReportSchedule, MetricsCollector, MetricDefinition, MetricValue,
    PerformanceKPI, ReportType, ReportStatus, MetricType
)
from src.domain.events.analytics_events import (
    DashboardCreated, WidgetAdded, ReportDefinitionCreated, ReportExecutionStarted,
    ReportExecutionCompleted, MetricRegistered, KPICreated, KPIUpdated,
    AnalyticsAlertTriggered, ReportScheduled
)


class AnalyticsService:
    def __init__(self):
        self.dashboards: Dict[str, AnalyticsDashboard] = {}
        self.report_definitions: Dict[str, ReportDefinition] = {}
        self.report_executions: Dict[str, ReportExecution] = {}
        self.kpis: Dict[str, PerformanceKPI] = {}
        self.metrics_collector = MetricsCollector()
        self._domain_events: List = []
        
        # Inicializar métricas predeterminadas
        self._initialize_default_metrics()
        self._initialize_default_kpis()

    def create_dashboard(
        self,
        name: str,
        description: str,
        created_by: str
    ) -> AnalyticsDashboard:
        """Crear nuevo dashboard de analytics"""
        dashboard_id = str(uuid.uuid4())
        
        dashboard = AnalyticsDashboard(
            dashboard_id=dashboard_id,
            name=name,
            description=description,
            created_by=created_by
        )
        
        self.dashboards[dashboard_id] = dashboard
        
        self._add_domain_event(
            DashboardCreated(
                dashboard_id=dashboard_id,
                name=name,
                description=description,
                created_by=created_by,
                created_at=datetime.now()
            )
        )
        
        return dashboard

    def add_widget_to_dashboard(
        self,
        dashboard_id: str,
        title: str,
        widget_type: str,
        data_source: str,
        configuration: Dict[str, Any] = None
    ) -> AnalyticsWidget:
        """Agregar widget a dashboard"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            raise ValueError(f"Dashboard {dashboard_id} no encontrado")
        
        widget_id = str(uuid.uuid4())
        widget = AnalyticsWidget(
            widget_id=widget_id,
            title=title,
            widget_type=widget_type,
            data_source=data_source
        )
        
        if configuration:
            widget.update_configuration(configuration)
        
        dashboard.add_widget(widget)
        
        self._add_domain_event(
            WidgetAdded(
                dashboard_id=dashboard_id,
                widget_id=widget_id,
                widget_type=widget_type,
                title=title,
                added_by="system",  # En implementación real vendría del contexto de usuario
                added_at=datetime.now()
            )
        )
        
        return widget

    def create_report_definition(
        self,
        name: str,
        report_type: ReportType,
        description: str,
        data_sources: List[str],
        created_by: str,
        template_path: Optional[str] = None
    ) -> ReportDefinition:
        """Crear definición de reporte"""
        report_id = str(uuid.uuid4())
        
        report_def = ReportDefinition(
            report_id=report_id,
            name=name,
            report_type=report_type,
            description=description,
            created_by=created_by
        )
        
        report_def.data_sources = data_sources
        if template_path:
            report_def.template_path = template_path
        
        self.report_definitions[report_id] = report_def
        
        self._add_domain_event(
            ReportDefinitionCreated(
                report_id=report_id,
                name=name,
                report_type=report_type.value,
                created_by=created_by,
                created_at=datetime.now()
            )
        )
        
        return report_def

    def schedule_report(
        self,
        report_id: str,
        frequency: str,
        time_of_day: str,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None
    ) -> ReportSchedule:
        """Programar ejecución automática de reporte"""
        report_def = self.report_definitions.get(report_id)
        if not report_def:
            raise ValueError(f"Reporte {report_id} no encontrado")
        
        schedule = ReportSchedule(
            frequency=frequency,
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            day_of_month=day_of_month
        )
        
        next_run = schedule.calculate_next_run()
        report_def.set_schedule(schedule)
        
        self._add_domain_event(
            ReportScheduled(
                report_id=report_id,
                frequency=frequency,
                scheduled_by="system",
                next_run_time=next_run,
                scheduled_at=datetime.now()
            )
        )
        
        return schedule

    def execute_report(
        self,
        report_id: str,
        requested_by: str,
        parameters: Dict[str, Any] = None,
        output_format: str = "pdf"
    ) -> ReportExecution:
        """Ejecutar reporte de forma manual o programada"""
        report_def = self.report_definitions.get(report_id)
        if not report_def:
            raise ValueError(f"Reporte {report_id} no encontrado")
        
        if not report_def.can_generate():
            raise ValueError("El reporte no está configurado para generación")
        
        execution_id = str(uuid.uuid4())
        execution = ReportExecution(
            execution_id=execution_id,
            report_definition=report_def,
            requested_by=requested_by,
            parameters=parameters or {}
        )
        
        execution.output_format = output_format
        
        self.report_executions[execution_id] = execution
        
        self._add_domain_event(
            ReportExecutionStarted(
                execution_id=execution_id,
                report_id=report_id,
                report_name=report_def.name,
                requested_by=requested_by,
                parameters=execution.parameters,
                started_at=datetime.now()
            )
        )
        
        # Simular procesamiento del reporte
        self._process_report_execution(execution)
        
        return execution

    def register_metric(
        self,
        name: str,
        description: str,
        metric_type: MetricType,
        unit: str,
        tags: Dict[str, str] = None,
        retention_days: int = 90
    ) -> MetricDefinition:
        """Registrar nueva métrica para recolección"""
        metric_id = str(uuid.uuid4())
        
        metric = MetricDefinition(
            metric_id=metric_id,
            name=name,
            description=description,
            metric_type=metric_type,
            unit=unit,
            tags=tags or {},
            aggregation_period="hour",
            retention_days=retention_days
        )
        
        self.metrics_collector.register_metric(metric)
        
        self._add_domain_event(
            MetricRegistered(
                metric_id=metric_id,
                metric_name=name,
                metric_type=metric_type.value,
                unit=unit,
                retention_days=retention_days,
                registered_by="system",
                registered_at=datetime.now()
            )
        )
        
        return metric

    def record_metric_value(
        self,
        metric_name: str,
        value: Union[float, int],
        tags: Dict[str, str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Registrar valor de métrica"""
        # Buscar métrica por nombre
        metric_id = None
        for mid, metric in self.metrics_collector.metrics.items():
            if metric.name == metric_name:
                metric_id = mid
                break
        
        if not metric_id:
            raise ValueError(f"Métrica '{metric_name}' no encontrada")
        
        self.metrics_collector.record_metric(
            metric_id=metric_id,
            value=value,
            tags=tags,
            timestamp=timestamp
        )

    def create_kpi(
        self,
        name: str,
        description: str,
        target_value: float,
        unit: str
    ) -> PerformanceKPI:
        """Crear nuevo KPI de rendimiento"""
        kpi_id = str(uuid.uuid4())
        
        kpi = PerformanceKPI(
            kpi_id=kpi_id,
            name=name,
            description=description,
            target_value=target_value,
            unit=unit
        )
        
        self.kpis[kpi_id] = kpi
        
        self._add_domain_event(
            KPICreated(
                kpi_id=kpi_id,
                name=name,
                target_value=target_value,
                unit=unit,
                created_by="system",
                created_at=datetime.now()
            )
        )
        
        return kpi

    def update_kpi_value(
        self,
        kpi_id: str,
        new_value: float
    ) -> PerformanceKPI:
        """Actualizar valor de KPI"""
        kpi = self.kpis.get(kpi_id)
        if not kpi:
            raise ValueError(f"KPI {kpi_id} no encontrado")
        
        old_value = kpi.current_value
        kpi.update_value(new_value)
        
        self._add_domain_event(
            KPIUpdated(
                kpi_id=kpi_id,
                old_value=old_value,
                new_value=new_value,
                target_value=kpi.target_value,
                status=kpi.status,
                trend=kpi.trend,
                updated_at=datetime.now()
            )
        )
        
        return kpi

    def get_dashboard_summary(
        self,
        dashboard_id: str
    ) -> Dict[str, Any]:
        """Obtener resumen de dashboard con datos actuales"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            raise ValueError(f"Dashboard {dashboard_id} no encontrado")
        
        widgets_data = []
        for widget in dashboard.widgets:
            widget_data = widget.get_widget_data()
            # En implementación real, aquí se cargarían los datos reales del widget
            widgets_data.append(widget_data)
        
        return {
            "dashboard_id": dashboard_id,
            "name": dashboard.name,
            "description": dashboard.description,
            "created_by": dashboard.created_by,
            "widgets_count": len(dashboard.widgets),
            "widgets": widgets_data,
            "last_updated": dashboard.updated_at,
            "status": dashboard.status.value
        }

    def get_metrics_summary(
        self,
        start_time: datetime,
        end_time: datetime,
        metric_names: List[str] = None
    ) -> Dict[str, Any]:
        """Obtener resumen de métricas en período"""
        metrics_data = {}
        
        metrics_to_process = self.metrics_collector.metrics.values()
        if metric_names:
            metrics_to_process = [
                m for m in metrics_to_process 
                if m.name in metric_names
            ]
        
        for metric in metrics_to_process:
            values = self.metrics_collector.get_metric_values(
                metric.metric_id, start_time, end_time
            )
            
            if values:
                numeric_values = [v.value for v in values]
                metrics_data[metric.name] = {
                    "metric_id": metric.metric_id,
                    "count": len(values),
                    "sum": sum(numeric_values),
                    "avg": sum(numeric_values) / len(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "unit": metric.unit,
                    "last_value": numeric_values[-1] if numeric_values else None,
                    "last_timestamp": values[-1].timestamp if values else None
                }
        
        return {
            "period_start": start_time,
            "period_end": end_time,
            "metrics": metrics_data,
            "total_metrics": len(metrics_data)
        }

    def get_kpis_dashboard(self) -> Dict[str, Any]:
        """Obtener dashboard de todos los KPIs"""
        kpis_summary = []
        
        for kpi in self.kpis.values():
            kpis_summary.append(kpi.get_kpi_summary())
        
        # Calcular estadísticas generales
        total_kpis = len(kpis_summary)
        on_target = len([k for k in kpis_summary if k["status"] == "on_target"])
        below_target = len([k for k in kpis_summary if k["status"] == "below_target"])
        
        return {
            "total_kpis": total_kpis,
            "on_target": on_target,
            "below_target": below_target,
            "performance_rate": (on_target / total_kpis * 100) if total_kpis > 0 else 0,
            "kpis": kpis_summary,
            "last_updated": datetime.now()
        }

    def get_reports_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los reportes"""
        reports_summary = []
        
        for report_def in self.report_definitions.values():
            # Obtener últimas ejecuciones
            recent_executions = [
                exec for exec in self.report_executions.values()
                if exec.report_definition.report_id == report_def.report_id
            ]
            
            recent_executions.sort(key=lambda x: x.created_at, reverse=True)
            last_execution = recent_executions[0] if recent_executions else None
            
            report_summary = {
                "report_id": report_def.report_id,
                "name": report_def.name,
                "type": report_def.report_type.value,
                "is_scheduled": report_def.schedule is not None,
                "next_run": report_def.schedule.next_run_time if report_def.schedule else None,
                "last_execution": {
                    "execution_id": last_execution.execution_id,
                    "status": last_execution.status.value,
                    "created_at": last_execution.created_at,
                    "execution_time": last_execution.execution_time_seconds
                } if last_execution else None,
                "total_executions": len(recent_executions)
            }
            
            reports_summary.append(report_summary)
        
        return {
            "total_reports": len(reports_summary),
            "scheduled_reports": len([r for r in reports_summary if r["is_scheduled"]]),
            "reports": reports_summary
        }

    def _process_report_execution(self, execution: ReportExecution) -> None:
        """Procesar ejecución de reporte (simulado)"""
        try:
            execution.start_execution()
            
            # Simular procesamiento
            import time
            time.sleep(0.1)  # Simular tiempo de procesamiento
            
            # Simular generación de archivo
            file_path = f"/reports/{execution.execution_id}.{execution.output_format}"
            file_size = 1024 * 100  # 100KB simulado
            
            execution.complete_execution(file_path, file_size)
            
            self._add_domain_event(
                ReportExecutionCompleted(
                    execution_id=execution.execution_id,
                    report_id=execution.report_definition.report_id,
                    execution_time_seconds=execution.execution_time_seconds or 0,
                    file_size_bytes=file_size,
                    output_format=execution.output_format,
                    completed_at=datetime.now()
                )
            )
            
        except Exception as e:
            execution.fail_execution(str(e))
            
            self._add_domain_event(
                AnalyticsAlertTriggered(
                    alert_id=str(uuid.uuid4()),
                    alert_type="report_failure",
                    severity="critical",
                    message=f"Falló la ejecución del reporte {execution.report_definition.name}",
                    affected_entities=[execution.report_definition.report_id],
                    triggered_at=datetime.now()
                )
            )

    def _initialize_default_metrics(self) -> None:
        """Inicializar métricas predeterminadas del sistema"""
        default_metrics = [
            ("orders_total", "Total de órdenes", MetricType.COUNTER, "count"),
            ("revenue_total", "Ingresos totales", MetricType.COUNTER, "currency"),
            ("active_customers", "Clientes activos", MetricType.GAUGE, "count"),
            ("delivery_time_avg", "Tiempo promedio de entrega", MetricType.GAUGE, "hours"),
            ("customer_satisfaction", "Satisfacción del cliente", MetricType.GAUGE, "rating"),
            ("order_fulfillment_rate", "Tasa de cumplimiento", MetricType.GAUGE, "percentage"),
            ("api_response_time", "Tiempo de respuesta API", MetricType.HISTOGRAM, "milliseconds"),
            ("error_rate", "Tasa de errores", MetricType.GAUGE, "percentage")
        ]
        
        for name, description, metric_type, unit in default_metrics:
            try:
                self.register_metric(name, description, metric_type, unit)
            except:
                pass  # Métrica ya existe

    def _initialize_default_kpis(self) -> None:
        """Inicializar KPIs predeterminados del sistema"""
        default_kpis = [
            ("customer_retention_rate", "Tasa de retención de clientes", 85.0, "percentage"),
            ("on_time_delivery_rate", "Tasa de entrega a tiempo", 95.0, "percentage"),
            ("monthly_revenue_growth", "Crecimiento mensual de ingresos", 10.0, "percentage"),
            ("customer_acquisition_cost", "Costo de adquisición de clientes", 25.0, "currency"),
            ("average_order_value", "Valor promedio de orden", 150.0, "currency"),
            ("operational_efficiency", "Eficiencia operacional", 90.0, "percentage")
        ]
        
        for name, description, target, unit in default_kpis:
            try:
                self.create_kpi(name, description, target, unit)
            except:
                pass  # KPI ya existe

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()