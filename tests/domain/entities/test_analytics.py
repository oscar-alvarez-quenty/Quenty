import pytest
from datetime import datetime, timedelta
from src.domain.entities.analytics import (
    AnalyticsDashboard, AnalyticsWidget, ReportDefinition, ReportExecution,
    MetricDefinition, KPI, DashboardStatus, ReportType, MetricType, ExecutionStatus
)


class TestAnalyticsDashboard:
    def test_create_analytics_dashboard(self):
        """Test creating an analytics dashboard"""
        dashboard_id = "dash_001"
        name = "Sales Dashboard"
        description = "Dashboard for sales metrics"
        created_by = "user_001"
        
        dashboard = AnalyticsDashboard(
            dashboard_id=dashboard_id,
            name=name,
            description=description,
            created_by=created_by
        )
        
        assert dashboard.dashboard_id == dashboard_id
        assert dashboard.name == name
        assert dashboard.description == description
        assert dashboard.created_by == created_by
        assert dashboard.status == DashboardStatus.ACTIVE
        assert dashboard.widgets == []
        assert dashboard.permissions == "private"

    def test_add_widget(self):
        """Test adding widget to dashboard"""
        dashboard = self._create_sample_dashboard()
        widget = AnalyticsWidget(
            widget_id="widget_001",
            title="Sales Chart",
            widget_type="chart",
            data_source="sales_db"
        )
        
        dashboard.add_widget(widget)
        
        assert len(dashboard.widgets) == 1
        assert dashboard.widgets[0] == widget

    def test_remove_widget(self):
        """Test removing widget from dashboard"""
        dashboard = self._create_sample_dashboard()
        widget = AnalyticsWidget(
            widget_id="widget_001",
            title="Sales Chart",
            widget_type="chart",
            data_source="sales_db"
        )
        dashboard.add_widget(widget)
        
        dashboard.remove_widget("widget_001")
        
        assert len(dashboard.widgets) == 0

    def test_update_layout(self):
        """Test updating dashboard layout"""
        dashboard = self._create_sample_dashboard()
        layout_config = {
            "columns": 2,
            "rows": 3,
            "widget_positions": {"widget_001": {"x": 0, "y": 0}}
        }
        
        dashboard.update_layout(layout_config)
        
        assert dashboard.layout == layout_config

    def test_set_permissions(self):
        """Test setting dashboard permissions"""
        dashboard = self._create_sample_dashboard()
        
        dashboard.set_permissions("public")
        assert dashboard.permissions == "public"
        
        dashboard.set_permissions("restricted")
        assert dashboard.permissions == "restricted"

    def test_archive_dashboard(self):
        """Test archiving dashboard"""
        dashboard = self._create_sample_dashboard()
        
        dashboard.archive_dashboard()
        
        assert dashboard.status == DashboardStatus.ARCHIVED
        assert dashboard.archived_at is not None

    def test_activate_dashboard(self):
        """Test activating dashboard"""
        dashboard = self._create_sample_dashboard()
        dashboard.archive_dashboard()
        
        dashboard.activate_dashboard()
        
        assert dashboard.status == DashboardStatus.ACTIVE

    def test_get_widget_count(self):
        """Test getting widget count"""
        dashboard = self._create_sample_dashboard()
        
        assert dashboard.get_widget_count() == 0
        
        widget = AnalyticsWidget(
            widget_id="widget_001",
            title="Sales Chart",
            widget_type="chart",
            data_source="sales_db"
        )
        dashboard.add_widget(widget)
        
        assert dashboard.get_widget_count() == 1

    def _create_sample_dashboard(self):
        """Helper method to create a sample dashboard"""
        return AnalyticsDashboard(
            dashboard_id="dash_001",
            name="Sales Dashboard",
            description="Dashboard for sales metrics",
            created_by="user_001"
        )


class TestAnalyticsWidget:
    def test_create_analytics_widget(self):
        """Test creating an analytics widget"""
        widget_id = "widget_001"
        title = "Sales Chart"
        widget_type = "chart"
        data_source = "sales_db"
        
        widget = AnalyticsWidget(
            widget_id=widget_id,
            title=title,
            widget_type=widget_type,
            data_source=data_source
        )
        
        assert widget.widget_id == widget_id
        assert widget.title == title
        assert widget.widget_type == widget_type
        assert widget.data_source == data_source
        assert widget.is_enabled == True
        assert widget.position == {"x": 0, "y": 0, "width": 1, "height": 1}
        assert widget.configuration == {}

    def test_update_configuration(self):
        """Test updating widget configuration"""
        widget = self._create_sample_widget()
        config = {
            "chart_type": "bar",
            "colors": ["#ff0000", "#00ff00"],
            "show_legend": True
        }
        
        widget.update_configuration(config)
        
        assert widget.configuration == config

    def test_set_position(self):
        """Test setting widget position"""
        widget = self._create_sample_widget()
        position = {"x": 2, "y": 1, "width": 2, "height": 3}
        
        widget.set_position(position)
        
        assert widget.position == position

    def test_enable_disable_widget(self):
        """Test enabling and disabling widget"""
        widget = self._create_sample_widget()
        
        widget.disable_widget()
        assert widget.is_enabled == False
        
        widget.enable_widget()
        assert widget.is_enabled == True

    def test_update_data_source(self):
        """Test updating data source"""
        widget = self._create_sample_widget()
        new_source = "updated_sales_db"
        
        widget.update_data_source(new_source)
        
        assert widget.data_source == new_source

    def test_get_widget_summary(self):
        """Test getting widget summary"""
        widget = self._create_sample_widget()
        widget.update_configuration({"chart_type": "bar"})
        
        summary = widget.get_widget_summary()
        
        assert summary["widget_id"] == widget.widget_id
        assert summary["title"] == widget.title
        assert summary["widget_type"] == widget.widget_type
        assert summary["is_enabled"] == widget.is_enabled
        assert summary["configuration"] == widget.configuration

    def _create_sample_widget(self):
        """Helper method to create a sample widget"""
        return AnalyticsWidget(
            widget_id="widget_001",
            title="Sales Chart",
            widget_type="chart",
            data_source="sales_db"
        )


class TestReportDefinition:
    def test_create_report_definition(self):
        """Test creating a report definition"""
        report_id = "report_001"
        name = "Monthly Sales Report"
        report_type = ReportType.SCHEDULED
        description = "Monthly sales summary"
        data_sources = ["sales_db", "customer_db"]
        created_by = "admin_001"
        
        report = ReportDefinition(
            report_id=report_id,
            name=name,
            report_type=report_type,
            description=description,
            data_sources=data_sources,
            created_by=created_by
        )
        
        assert report.report_id == report_id
        assert report.name == name
        assert report.report_type == report_type
        assert report.description == description
        assert report.data_sources == data_sources
        assert report.created_by == created_by
        assert report.is_active == True
        assert report.schedule is None

    def test_set_schedule(self):
        """Test setting report schedule"""
        report = self._create_sample_report()
        schedule = {
            "frequency": "monthly",
            "day_of_month": 1,
            "time": "09:00",
            "timezone": "UTC"
        }
        
        report.set_schedule(schedule)
        
        assert report.schedule == schedule

    def test_update_template(self):
        """Test updating report template"""
        report = self._create_sample_report()
        template_path = "/templates/monthly_sales.html"
        
        report.update_template(template_path)
        
        assert report.template_path == template_path

    def test_activate_deactivate_report(self):
        """Test activating and deactivating report"""
        report = self._create_sample_report()
        
        report.deactivate_report()
        assert report.is_active == False
        
        report.activate_report()
        assert report.is_active == True

    def test_add_parameter(self):
        """Test adding report parameter"""
        report = self._create_sample_report()
        param_name = "start_date"
        param_config = {"type": "date", "required": True, "default": "2023-01-01"}
        
        report.add_parameter(param_name, param_config)
        
        assert param_name in report.parameters
        assert report.parameters[param_name] == param_config

    def test_remove_parameter(self):
        """Test removing report parameter"""
        report = self._create_sample_report()
        report.add_parameter("start_date", {"type": "date"})
        
        report.remove_parameter("start_date")
        
        assert "start_date" not in report.parameters

    def test_validate_parameters(self):
        """Test validating report parameters"""
        report = self._create_sample_report()
        report.add_parameter("start_date", {"type": "date", "required": True})
        report.add_parameter("end_date", {"type": "date", "required": False})
        
        # Valid parameters
        params = {"start_date": "2023-01-01", "end_date": "2023-01-31"}
        is_valid, errors = report.validate_parameters(params)
        assert is_valid == True
        assert len(errors) == 0
        
        # Missing required parameter
        params = {"end_date": "2023-01-31"}
        is_valid, errors = report.validate_parameters(params)
        assert is_valid == False
        assert "start_date is required" in errors

    def _create_sample_report(self):
        """Helper method to create a sample report definition"""
        return ReportDefinition(
            report_id="report_001",
            name="Monthly Sales Report",
            report_type=ReportType.SCHEDULED,
            description="Monthly sales summary",
            data_sources=["sales_db", "customer_db"],
            created_by="admin_001"
        )


class TestReportExecution:
    def test_create_report_execution(self):
        """Test creating a report execution"""
        execution_id = "exec_001"
        report_id = "report_001"
        requested_by = "user_001"
        parameters = {"start_date": "2023-01-01", "end_date": "2023-01-31"}
        
        execution = ReportExecution(
            execution_id=execution_id,
            report_id=report_id,
            requested_by=requested_by,
            parameters=parameters
        )
        
        assert execution.execution_id == execution_id
        assert execution.report_id == report_id
        assert execution.requested_by == requested_by
        assert execution.parameters == parameters
        assert execution.status == ExecutionStatus.PENDING
        assert execution.file_path is None
        assert execution.execution_time_seconds is None

    def test_start_execution(self):
        """Test starting report execution"""
        execution = self._create_sample_execution()
        
        execution.start_execution()
        
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.started_at is not None

    def test_complete_execution(self):
        """Test completing report execution"""
        execution = self._create_sample_execution()
        execution.start_execution()
        
        file_path = "/reports/exec_001.pdf"
        execution.complete_execution(file_path)
        
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.file_path == file_path
        assert execution.completed_at is not None
        assert execution.execution_time_seconds is not None

    def test_fail_execution(self):
        """Test failing report execution"""
        execution = self._create_sample_execution()
        execution.start_execution()
        
        error_message = "Database connection failed"
        execution.fail_execution(error_message)
        
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_message == error_message
        assert execution.failed_at is not None

    def test_cancel_execution(self):
        """Test canceling report execution"""
        execution = self._create_sample_execution()
        execution.start_execution()
        
        execution.cancel_execution()
        
        assert execution.status == ExecutionStatus.CANCELLED
        assert execution.cancelled_at is not None

    def test_calculate_execution_time(self):
        """Test calculating execution time"""
        execution = self._create_sample_execution()
        execution.start_execution()
        
        # Simulate some processing time
        import time
        time.sleep(0.1)
        
        execution.complete_execution("/path/to/report.pdf")
        
        assert execution.execution_time_seconds > 0

    def _create_sample_execution(self):
        """Helper method to create a sample report execution"""
        return ReportExecution(
            execution_id="exec_001",
            report_id="report_001",
            requested_by="user_001",
            parameters={"start_date": "2023-01-01", "end_date": "2023-01-31"}
        )


class TestMetricDefinition:
    def test_create_metric_definition(self):
        """Test creating a metric definition"""
        metric_id = "metric_001"
        name = "order_count"
        description = "Total number of orders"
        metric_type = MetricType.COUNTER
        unit = "orders"
        
        metric = MetricDefinition(
            metric_id=metric_id,
            name=name,
            description=description,
            metric_type=metric_type,
            unit=unit
        )
        
        assert metric.metric_id == metric_id
        assert metric.name == name
        assert metric.description == description
        assert metric.metric_type == metric_type
        assert metric.unit == unit
        assert metric.tags == {}
        assert metric.retention_days == 90

    def test_add_tag(self):
        """Test adding tag to metric"""
        metric = self._create_sample_metric()
        
        metric.add_tag("environment", "production")
        
        assert "environment" in metric.tags
        assert metric.tags["environment"] == "production"

    def test_remove_tag(self):
        """Test removing tag from metric"""
        metric = self._create_sample_metric()
        metric.add_tag("environment", "production")
        
        metric.remove_tag("environment")
        
        assert "environment" not in metric.tags

    def test_update_retention(self):
        """Test updating retention period"""
        metric = self._create_sample_metric()
        new_retention = 180
        
        metric.update_retention(new_retention)
        
        assert metric.retention_days == new_retention

    def test_is_expired(self):
        """Test checking if metric data is expired"""
        metric = self._create_sample_metric()
        
        # Recent timestamp
        recent_timestamp = datetime.now() - timedelta(days=30)
        assert metric.is_expired(recent_timestamp) == False
        
        # Old timestamp
        old_timestamp = datetime.now() - timedelta(days=100)
        assert metric.is_expired(old_timestamp) == True

    def test_validate_value(self):
        """Test validating metric value"""
        # Counter metric - should be non-negative
        counter_metric = MetricDefinition(
            metric_id="counter_001",
            name="requests",
            description="Request count",
            metric_type=MetricType.COUNTER,
            unit="requests"
        )
        
        assert counter_metric.validate_value(10) == True
        assert counter_metric.validate_value(-1) == False
        
        # Gauge metric - can be any number
        gauge_metric = MetricDefinition(
            metric_id="gauge_001",
            name="temperature",
            description="Temperature reading",
            metric_type=MetricType.GAUGE,
            unit="celsius"
        )
        
        assert gauge_metric.validate_value(25.5) == True
        assert gauge_metric.validate_value(-10.0) == True

    def _create_sample_metric(self):
        """Helper method to create a sample metric definition"""
        return MetricDefinition(
            metric_id="metric_001",
            name="order_count",
            description="Total number of orders",
            metric_type=MetricType.COUNTER,
            unit="orders"
        )


class TestKPI:
    def test_create_kpi(self):
        """Test creating a KPI"""
        kpi_id = "kpi_001"
        name = "Monthly Revenue"
        description = "Total monthly revenue"
        target_value = 100000.0
        unit = "COP"
        
        kpi = KPI(
            kpi_id=kpi_id,
            name=name,
            description=description,
            target_value=target_value,
            unit=unit
        )
        
        assert kpi.kpi_id == kpi_id
        assert kpi.name == name
        assert kpi.description == description
        assert kpi.target_value == target_value
        assert kpi.unit == unit
        assert kpi.current_value is None
        assert kpi.status == "not_set"
        assert kpi.trend is None

    def test_update_value(self):
        """Test updating KPI value"""
        kpi = self._create_sample_kpi()
        new_value = 95000.0
        
        kpi.update_value(new_value)
        
        assert kpi.current_value == new_value
        assert kpi.status == "below_target"
        assert kpi.last_updated is not None

    def test_calculate_performance_percentage(self):
        """Test calculating performance percentage"""
        kpi = self._create_sample_kpi()
        
        # No current value
        assert kpi.get_performance_percentage() is None
        
        # Below target
        kpi.update_value(80000.0)
        assert kpi.get_performance_percentage() == 80.0
        
        # Above target
        kpi.update_value(120000.0)
        assert kpi.get_performance_percentage() == 120.0

    def test_determine_status(self):
        """Test determining KPI status"""
        kpi = self._create_sample_kpi()
        
        # On target (within 5% tolerance)
        kpi.update_value(98000.0)
        status = kpi.determine_status()
        assert status == "on_target"
        
        # Below target
        kpi.update_value(85000.0)
        status = kpi.determine_status()
        assert status == "below_target"
        
        # Above target
        kpi.update_value(110000.0)
        status = kpi.determine_status()
        assert status == "above_target"

    def test_set_target(self):
        """Test setting new target value"""
        kpi = self._create_sample_kpi()
        new_target = 120000.0
        reason = "Market expansion"
        
        kpi.set_target(new_target, reason)
        
        assert kpi.target_value == new_target
        assert len(kpi.target_history) == 1
        history_entry = kpi.target_history[0]
        assert history_entry["new_target"] == new_target
        assert history_entry["reason"] == reason

    def test_add_value_history(self):
        """Test adding value to history"""
        kpi = self._create_sample_kpi()
        
        # Add multiple values to track trend
        kpi.update_value(90000.0)
        kpi.update_value(95000.0)
        kpi.update_value(100000.0)
        
        assert len(kpi.value_history) == 3
        assert kpi.trend == "improving"

    def test_calculate_trend(self):
        """Test calculating trend"""
        kpi = self._create_sample_kpi()
        
        # Improving trend
        kpi.value_history = [
            {"value": 80000.0, "timestamp": datetime.now() - timedelta(days=2)},
            {"value": 90000.0, "timestamp": datetime.now() - timedelta(days=1)},
            {"value": 100000.0, "timestamp": datetime.now()}
        ]
        trend = kpi.calculate_trend()
        assert trend == "improving"
        
        # Declining trend
        kpi.value_history = [
            {"value": 100000.0, "timestamp": datetime.now() - timedelta(days=2)},
            {"value": 90000.0, "timestamp": datetime.now() - timedelta(days=1)},
            {"value": 80000.0, "timestamp": datetime.now()}
        ]
        trend = kpi.calculate_trend()
        assert trend == "declining"

    def test_is_critical(self):
        """Test checking if KPI is in critical state"""
        kpi = self._create_sample_kpi()
        
        # Not critical when on target
        kpi.update_value(98000.0)
        assert kpi.is_critical() == False
        
        # Critical when significantly below target
        kpi.update_value(70000.0)  # 30% below target
        assert kpi.is_critical() == True

    def test_get_kpi_summary(self):
        """Test getting KPI summary"""
        kpi = self._create_sample_kpi()
        kpi.update_value(95000.0)
        
        summary = kpi.get_kpi_summary()
        
        assert summary["kpi_id"] == kpi.kpi_id
        assert summary["name"] == kpi.name
        assert summary["target_value"] == kpi.target_value
        assert summary["current_value"] == kpi.current_value
        assert summary["status"] == kpi.status
        assert summary["performance_percentage"] == 95.0

    def _create_sample_kpi(self):
        """Helper method to create a sample KPI"""
        return KPI(
            kpi_id="kpi_001",
            name="Monthly Revenue",
            description="Total monthly revenue",
            target_value=100000.0,
            unit="COP"
        )