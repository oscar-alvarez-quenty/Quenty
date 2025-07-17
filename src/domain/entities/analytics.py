"""Entidades de dominio para gestión de analíticas y reportes.

Este módulo contiene las entidades para manejar dashboards, widgets, reportes,
métricas, KPIs y toda la funcionalidad de business intelligence de la plataforma.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime, timedelta
import uuid

from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class ReportType(Enum):
    """Tipos de reportes disponibles en el sistema.
    
    Attributes:
        SALES: Reportes de ventas e ingresos
        OPERATIONAL: Reportes operacionales y logísticos
        FINANCIAL: Reportes financieros y contables
        CUSTOMER: Reportes de clientes y comportamiento
        PERFORMANCE: Reportes de rendimiento y KPIs
        COMPLIANCE: Reportes de cumplimiento regulatorio
    """
    SALES = "sales"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"


class ReportStatus(Enum):
    """Estados de generación de reportes.
    
    Attributes:
        PENDING: Reporte en cola esperando procesamiento
        GENERATING: Reporte en proceso de generación
        COMPLETED: Reporte generado exitosamente
        FAILED: Error en la generación del reporte
        SCHEDULED: Reporte programado para ejecución futura
    """
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class AnalyticsStatus(Enum):
    """Estados de componentes de analíticas.
    
    Attributes:
        ACTIVE: Componente activo y funcionando
        INACTIVE: Componente desactivado
        PROCESSING: Componente procesando datos
        ERROR: Componente con errores
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
    ERROR = "error"


class MetricType(Enum):
    """Tipos de métricas disponibles.
    
    Attributes:
        COUNTER: Métrica de contador (solo incrementa)
        GAUGE: Métrica de medidor (puede subir y bajar)
        HISTOGRAM: Métrica de histograma para distribuciones
        SUMMARY: Métrica de resumen con percentiles
    """
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricDefinition:
    """Definición de una métrica del sistema.
    
    Define los metadatos y configuración de una métrica
    que se recopilará y analizará en el sistema.
    
    Attributes:
        metric_id: Identificador único de la métrica
        name: Nombre descriptivo
        description: Descripción detallada
        metric_type: Tipo de métrica (counter, gauge, etc.)
        unit: Unidad de medida
        tags: Etiquetas para categorización
        aggregation_period: Período de agregación
        retention_days: Días de retención de datos
    """
    metric_id: str
    name: str
    description: str
    metric_type: MetricType
    unit: str
    tags: Dict[str, str]
    aggregation_period: str  # "minute", "hour", "day", "week", "month"
    retention_days: int = 90


@dataclass
class MetricValue:
    """Valor individual de una métrica.
    
    Representa un punto de datos con timestamp
    para una métrica específica.
    
    Attributes:
        metric_id: ID de la métrica asociada
        timestamp: Momento de la medición
        value: Valor numérico de la métrica
        tags: Etiquetas adicionales
        dimensions: Dimensiones para agrupación
    """
    metric_id: str
    timestamp: datetime
    value: Union[float, int]
    tags: Dict[str, str] = None
    dimensions: Dict[str, Any] = None


class AnalyticsDashboard:
    """Dashboard de analíticas para visualización de datos.
    
    Agrupa widgets y visualizaciones para proporcionar
    una vista consolidada de métricas y KPIs del negocio.
    
    Attributes:
        dashboard_id: Identificador único del dashboard
        name: Nombre del dashboard
        description: Descripción del propósito
        created_by: Usuario que creó el dashboard
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        widgets: Lista de widgets incluidos
        is_public: Indica si es público o privado
        permissions: Permisos de acceso por usuario
        refresh_interval_minutes: Intervalo de actualización
        status: Estado actual del dashboard
    """
    
    def __init__(
        self,
        dashboard_id: str,
        name: str,
        description: str,
        created_by: str
    ):
        self.dashboard_id = dashboard_id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.widgets: List[AnalyticsWidget] = []
        self.is_public = False
        self.permissions: Dict[str, List[str]] = {}  # user_id -> permissions
        self.refresh_interval_minutes = 15
        self.status = AnalyticsStatus.ACTIVE

    def add_widget(self, widget: 'AnalyticsWidget') -> None:
        """Agrega un widget al dashboard.
        
        Args:
            widget: Widget a agregar al dashboard
            
        Raises:
            ValueError: Si el widget ya existe en el dashboard
        """
        # Verificar que el widget no exista ya
        existing_widget = next((w for w in self.widgets if w.widget_id == widget.widget_id), None)
        if existing_widget:
            raise ValueError(f"Widget {widget.widget_id} ya existe en el dashboard")
            
        self.widgets.append(widget)
        self.updated_at = datetime.now()

    def remove_widget(self, widget_id: str) -> bool:
        """Remueve un widget del dashboard.
        
        Args:
            widget_id: ID del widget a remover
            
        Returns:
            bool: True si el widget fue removido, False si no existía
        """
        original_count = len(self.widgets)
        self.widgets = [w for w in self.widgets if w.widget_id != widget_id]
        
        if len(self.widgets) < original_count:
            self.updated_at = datetime.now()
            return True
        return False

    def update_widget_position(self, widget_id: str, position: Dict[str, int]) -> bool:
        """Actualiza la posición de un widget en el dashboard.
        
        Args:
            widget_id: ID del widget a reposicionar
            position: Nueva posición (x, y, width, height)
            
        Returns:
            bool: True si se actualizó, False si el widget no existe
            
        Raises:
            ValueError: Si la posición es inválida
        """
        required_keys = ['x', 'y', 'width', 'height']
        if not all(key in position for key in required_keys):
            raise ValueError(f"La posición debe incluir: {required_keys}")
            
        for widget in self.widgets:
            if widget.widget_id == widget_id:
                widget.position = position
                self.updated_at = datetime.now()
                return True
        return False

    def grant_permission(self, user_id: str, permissions: List[str]) -> None:
        """Otorga permisos de acceso a un usuario.
        
        Args:
            user_id: ID del usuario
            permissions: Lista de permisos a otorgar
        """
        valid_permissions = ['read', 'write', 'admin', 'share']
        invalid_perms = [p for p in permissions if p not in valid_permissions]
        if invalid_perms:
            raise ValueError(f"Permisos inválidos: {invalid_perms}")
            
        self.permissions[user_id] = permissions
        self.updated_at = datetime.now()

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Verifica si un usuario tiene un permiso específico.
        
        El creador del dashboard siempre tiene todos los permisos.
        
        Args:
            user_id: ID del usuario a verificar
            permission: Permiso a verificar
            
        Returns:
            bool: True si tiene el permiso
        """
        if self.created_by == user_id:
            return True
        
        user_permissions = self.permissions.get(user_id, [])
        return permission in user_permissions or "admin" in user_permissions


class AnalyticsWidget:
    """Widget individual para dashboards de analíticas.
    
    Representa un componente visual que muestra datos
    específicos en un dashboard, como gráficos, tablas o métricas.
    
    Attributes:
        widget_id: Identificador único del widget
        title: Título mostrado en el widget
        widget_type: Tipo de visualización (chart, table, metric, gauge)
        data_source: Fuente de datos para el widget
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        configuration: Configuración específica del widget
        position: Posición y tamaño en el dashboard
        is_enabled: Indica si el widget está habilitado
        refresh_interval_seconds: Intervalo de actualización en segundos
    """
    
    def __init__(
        self,
        widget_id: str,
        title: str,
        widget_type: str,
        data_source: str
    ):
        self.widget_id = widget_id
        self.title = title
        self.widget_type = widget_type  # "chart", "table", "metric", "gauge"
        self.data_source = data_source
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.configuration: Dict[str, Any] = {}
        self.position: Dict[str, int] = {"x": 0, "y": 0, "width": 4, "height": 3}
        self.is_enabled = True
        self.refresh_interval_seconds = 300  # 5 minutos por defecto

    def update_configuration(self, config: Dict[str, Any]) -> None:
        """Actualiza la configuración del widget.
        
        Args:
            config: Diccionario con nueva configuración
        """
        self.configuration.update(config)
        self.updated_at = datetime.now()

    def get_widget_data(self) -> Dict[str, Any]:
        """Obtiene los datos del widget para visualización.
        
        En implementación real consultaría la fuente de datos
        configurada para obtener los datos actuales.
        
        Returns:
            Dict con la estructura de datos del widget
        """
        return {
            "widget_id": self.widget_id,
            "title": self.title,
            "type": self.widget_type,
            "data": [],
            "last_updated": self.updated_at
        }


class ReportDefinition:
    """Definición de un reporte del sistema.
    
    Define la estructura, parámetros y configuración
    de un reporte que puede ser generado bajo demanda
    o de forma programada.
    
    Attributes:
        report_id: Identificador único del reporte
        name: Nombre descriptivo del reporte
        report_type: Tipo de reporte (ventas, operacional, etc.)
        description: Descripción detallada del contenido
        created_by: Usuario que creó la definición
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        parameters: Parámetros configurables del reporte
        filters: Filtros aplicables
        data_sources: Fuentes de datos utilizadas
        schedule: Programación automática (opcional)
        output_formats: Formatos de salida soportados
        is_active: Indica si el reporte está activo
        template_path: Ruta de la plantilla del reporte
    """
    
    def __init__(
        self,
        report_id: str,
        name: str,
        report_type: ReportType,
        description: str,
        created_by: str
    ):
        self.report_id = report_id
        self.name = name
        self.report_type = report_type
        self.description = description
        self.created_by = created_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.parameters: Dict[str, Any] = {}
        self.filters: Dict[str, Any] = {}
        self.data_sources: List[str] = []
        self.schedule: Optional['ReportSchedule'] = None
        self.output_formats: List[str] = ["pdf", "excel", "csv"]
        self.is_active = True
        self.template_path: Optional[str] = None

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Establece los parámetros del reporte.
        
        Args:
            parameters: Diccionario con parámetros del reporte
        """
        self.parameters = parameters
        self.updated_at = datetime.now()

    def add_filter(self, filter_name: str, filter_value: Any) -> None:
        """Agrega un filtro al reporte.
        
        Args:
            filter_name: Nombre del filtro
            filter_value: Valor del filtro
        """
        self.filters[filter_name] = filter_value
        self.updated_at = datetime.now()

    def set_schedule(self, schedule: 'ReportSchedule') -> None:
        """Establece la programación automática del reporte.
        
        Args:
            schedule: Configuración de programación
        """
        self.schedule = schedule
        self.updated_at = datetime.now()

    def can_generate(self) -> bool:
        """Verifica si el reporte puede ser generado.
        
        Returns:
            bool: True si el reporte está listo para generar
        """
        return (self.is_active and 
                len(self.data_sources) > 0 and
                self.template_path is not None)


@dataclass
class ReportSchedule:
    frequency: str  # "daily", "weekly", "monthly", "quarterly"
    time_of_day: str  # "09:00"
    day_of_week: Optional[int] = None  # 0-6 (Monday-Sunday)
    day_of_month: Optional[int] = None  # 1-31
    timezone: str = "UTC"
    is_enabled: bool = True
    next_run_time: Optional[datetime] = None

    def calculate_next_run(self) -> datetime:
        """Calcular próxima ejecución programada"""
        now = datetime.now()
        
        if self.frequency == "daily":
            next_run = now.replace(
                hour=int(self.time_of_day.split(":")[0]),
                minute=int(self.time_of_day.split(":")[1]),
                second=0,
                microsecond=0
            )
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif self.frequency == "weekly" and self.day_of_week is not None:
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=int(self.time_of_day.split(":")[0]),
                minute=int(self.time_of_day.split(":")[1]),
                second=0,
                microsecond=0
            )
        
        elif self.frequency == "monthly" and self.day_of_month is not None:
            next_run = now.replace(
                day=self.day_of_month,
                hour=int(self.time_of_day.split(":")[0]),
                minute=int(self.time_of_day.split(":")[1]),
                second=0,
                microsecond=0
            )
            if next_run <= now:
                # Próximo mes
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
        
        else:
            next_run = now + timedelta(days=1)
        
        self.next_run_time = next_run
        return next_run


class ReportExecution:
    def __init__(
        self,
        execution_id: str,
        report_definition: ReportDefinition,
        requested_by: str,
        parameters: Dict[str, Any] = None
    ):
        self.execution_id = execution_id
        self.report_definition = report_definition
        self.requested_by = requested_by
        self.parameters = parameters or {}
        self.status = ReportStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.file_path: Optional[str] = None
        self.file_size_bytes: Optional[int] = None
        self.output_format: str = "pdf"
        self.error_message: Optional[str] = None
        self.execution_time_seconds: Optional[float] = None

    def start_execution(self) -> None:
        """Iniciar ejecución del reporte"""
        if self.status != ReportStatus.PENDING:
            raise ValueError("Solo se pueden iniciar reportes pendientes")
        
        self.status = ReportStatus.GENERATING
        self.started_at = datetime.now()

    def complete_execution(self, file_path: str, file_size: int) -> None:
        """Completar ejecución exitosa"""
        if self.status != ReportStatus.GENERATING:
            raise ValueError("Solo se pueden completar reportes en generación")
        
        self.status = ReportStatus.COMPLETED
        self.completed_at = datetime.now()
        self.file_path = file_path
        self.file_size_bytes = file_size
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail_execution(self, error_message: str) -> None:
        """Marcar ejecución como fallida"""
        if self.status != ReportStatus.GENERATING:
            raise ValueError("Solo se pueden fallar reportes en generación")
        
        self.status = ReportStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        
        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def get_execution_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la ejecución"""
        return {
            "execution_id": self.execution_id,
            "report_name": self.report_definition.name,
            "report_type": self.report_definition.report_type.value,
            "status": self.status.value,
            "requested_by": self.requested_by,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time_seconds": self.execution_time_seconds,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "output_format": self.output_format,
            "error_message": self.error_message
        }


class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, MetricDefinition] = {}
        self.metric_values: List[MetricValue] = []
        self.retention_manager = MetricsRetentionManager()

    def register_metric(self, metric: MetricDefinition) -> None:
        """Registrar nueva métrica"""
        self.metrics[metric.metric_id] = metric

    def record_metric(
        self,
        metric_id: str,
        value: Union[float, int],
        tags: Dict[str, str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Registrar valor de métrica"""
        if metric_id not in self.metrics:
            raise ValueError(f"Métrica {metric_id} no registrada")
        
        metric_value = MetricValue(
            metric_id=metric_id,
            timestamp=timestamp or datetime.now(),
            value=value,
            tags=tags or {}
        )
        
        self.metric_values.append(metric_value)

    def get_metric_values(
        self,
        metric_id: str,
        start_time: datetime,
        end_time: datetime,
        tags: Dict[str, str] = None
    ) -> List[MetricValue]:
        """Obtener valores de métrica en rango de tiempo"""
        values = [
            mv for mv in self.metric_values
            if (mv.metric_id == metric_id and
                start_time <= mv.timestamp <= end_time)
        ]
        
        if tags:
            values = [
                mv for mv in values
                if all(mv.tags.get(k) == v for k, v in tags.items())
            ]
        
        return values

    def calculate_aggregated_metric(
        self,
        metric_id: str,
        aggregation: str,  # "sum", "avg", "min", "max", "count"
        start_time: datetime,
        end_time: datetime
    ) -> Optional[float]:
        """Calcular métrica agregada"""
        values = self.get_metric_values(metric_id, start_time, end_time)
        
        if not values:
            return None
        
        numeric_values = [v.value for v in values]
        
        if aggregation == "sum":
            return sum(numeric_values)
        elif aggregation == "avg":
            return sum(numeric_values) / len(numeric_values)
        elif aggregation == "min":
            return min(numeric_values)
        elif aggregation == "max":
            return max(numeric_values)
        elif aggregation == "count":
            return len(numeric_values)
        else:
            raise ValueError(f"Agregación {aggregation} no soportada")


class MetricsRetentionManager:
    def __init__(self):
        self.retention_policies: Dict[str, int] = {}  # metric_id -> retention_days

    def set_retention_policy(self, metric_id: str, retention_days: int) -> None:
        """Establecer política de retención para métrica"""
        self.retention_policies[metric_id] = retention_days

    def cleanup_expired_metrics(self, metric_values: List[MetricValue]) -> List[MetricValue]:
        """Limpiar métricas expiradas"""
        now = datetime.now()
        cleaned_values = []
        
        for value in metric_values:
            retention_days = self.retention_policies.get(value.metric_id, 90)
            retention_threshold = now - timedelta(days=retention_days)
            
            if value.timestamp >= retention_threshold:
                cleaned_values.append(value)
        
        return cleaned_values


class PerformanceKPI:
    def __init__(
        self,
        kpi_id: str,
        name: str,
        description: str,
        target_value: float,
        unit: str
    ):
        self.kpi_id = kpi_id
        self.name = name
        self.description = description
        self.target_value = target_value
        self.unit = unit
        self.current_value: Optional[float] = None
        self.last_updated: Optional[datetime] = None
        self.trend: Optional[str] = None  # "up", "down", "stable"
        self.status: str = "unknown"  # "on_target", "below_target", "above_target"

    def update_value(self, new_value: float) -> None:
        """Actualizar valor del KPI"""
        old_value = self.current_value
        self.current_value = new_value
        self.last_updated = datetime.now()
        
        # Calcular tendencia
        if old_value is not None:
            if new_value > old_value:
                self.trend = "up"
            elif new_value < old_value:
                self.trend = "down"
            else:
                self.trend = "stable"
        
        # Calcular estado vs objetivo
        if new_value >= self.target_value:
            self.status = "on_target"
        else:
            self.status = "below_target"

    def get_performance_percentage(self) -> Optional[float]:
        """Obtener porcentaje de cumplimiento del objetivo"""
        if self.current_value is None:
            return None
        
        return (self.current_value / self.target_value) * 100

    def get_kpi_summary(self) -> Dict[str, Any]:
        """Obtener resumen del KPI"""
        return {
            "kpi_id": self.kpi_id,
            "name": self.name,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "unit": self.unit,
            "performance_percentage": self.get_performance_percentage(),
            "status": self.status,
            "trend": self.trend,
            "last_updated": self.last_updated
        }