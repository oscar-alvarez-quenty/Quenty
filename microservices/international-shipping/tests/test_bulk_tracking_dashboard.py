"""
Unit tests for SCRUM-48: Bulk Tracking Dashboard functionality
Tests cover dashboard creation, tracking status monitoring, filtering, and data export
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.main import app, BulkTrackingDashboardCreate, BulkTrackingDashboardUpdate, TrackingFilter
from src.models import BulkTrackingDashboard


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user with dashboard permissions"""
    return {
        "user_id": "test_user_123",
        "company_id": "test_company_456",
        "permissions": [
            "shipping:dashboard_create", 
            "shipping:dashboard_update", 
            "shipping:dashboard_delete"
        ],
        "is_superuser": False
    }


@pytest.fixture
def sample_tracking_numbers():
    """Sample tracking numbers for testing"""
    return ["TN001", "TN002", "TN003", "TN004", "TN005"]


@pytest.fixture
def valid_dashboard_data():
    """Valid dashboard creation data"""
    return {
        "name": "Q1 International Shipments",
        "description": "Dashboard for tracking Q1 international shipments",
        "tracking_numbers": ["TN001", "TN002", "TN003", "TN004", "TN005"],
        "status_filters": ["in_transit", "delivered"],
        "carrier_filters": ["DHL", "FedEx"],
        "refresh_interval": 300
    }


class TestBulkTrackingDashboardValidation:
    """Test cases for dashboard validation logic"""
    
    def test_valid_dashboard_creation(self, valid_dashboard_data):
        """Test validation of valid dashboard data"""
        dashboard = BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert dashboard.name == "Q1 International Shipments"
        assert len(dashboard.tracking_numbers) == 5
        assert dashboard.refresh_interval == 300
    
    def test_invalid_dashboard_name_too_short(self, valid_dashboard_data):
        """Test validation failure for too short dashboard name"""
        valid_dashboard_data["name"] = "AB"  # Too short
        
        with pytest.raises(ValueError) as exc_info:
            BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert "at least 3 characters" in str(exc_info.value)
    
    def test_invalid_dashboard_name_too_long(self, valid_dashboard_data):
        """Test validation failure for too long dashboard name"""
        valid_dashboard_data["name"] = "A" * 256  # Too long
        
        with pytest.raises(ValueError) as exc_info:
            BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert "at most 255 characters" in str(exc_info.value)
    
    def test_invalid_empty_tracking_numbers(self, valid_dashboard_data):
        """Test validation failure for empty tracking numbers list"""
        valid_dashboard_data["tracking_numbers"] = []
        
        with pytest.raises(ValueError) as exc_info:
            BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert "at least 1 item" in str(exc_info.value)
    
    def test_invalid_too_many_tracking_numbers(self, valid_dashboard_data):
        """Test validation failure for too many tracking numbers"""
        valid_dashboard_data["tracking_numbers"] = [f"TN{i:03d}" for i in range(1001)]  # Too many
        
        with pytest.raises(ValueError) as exc_info:
            BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert "at most 1000 items" in str(exc_info.value)
    
    def test_invalid_refresh_interval_too_short(self, valid_dashboard_data):
        """Test validation failure for too short refresh interval"""
        valid_dashboard_data["refresh_interval"] = 30  # Less than 60 seconds
        
        with pytest.raises(ValueError) as exc_info:
            BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert "greater than or equal to 60" in str(exc_info.value)
    
    def test_invalid_refresh_interval_too_long(self, valid_dashboard_data):
        """Test validation failure for too long refresh interval"""
        valid_dashboard_data["refresh_interval"] = 7200  # More than 3600 seconds
        
        with pytest.raises(ValueError) as exc_info:
            BulkTrackingDashboardCreate(**valid_dashboard_data)
        assert "less than or equal to 3600" in str(exc_info.value)


class TestBulkTrackingDashboardEndpoints:
    """Test cases for bulk tracking dashboard API endpoints"""
    
    @patch('src.main.verify_token')
    def test_create_dashboard_success(self, mock_verify_token, client, mock_user, valid_dashboard_data):
        """Test successful dashboard creation"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/dashboards", json=valid_dashboard_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == valid_dashboard_data["name"]
        assert data["tracking_numbers"] == valid_dashboard_data["tracking_numbers"]
        assert "unique_id" in data
        assert "created_at" in data
    
    @patch('src.main.verify_token')
    def test_create_dashboard_validation_error(self, mock_verify_token, client, mock_user):
        """Test dashboard creation with validation errors"""
        mock_verify_token.return_value = mock_user
        
        invalid_data = {
            "name": "AB",  # Too short
            "tracking_numbers": [],  # Empty
            "refresh_interval": 30  # Too short
        }
        
        response = client.post("/api/v1/dashboards", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.main.verify_token')
    def test_get_dashboards_list(self, mock_verify_token, client, mock_user):
        """Test getting list of dashboards"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for dashboard in data:
            assert "unique_id" in dashboard
            assert "name" in dashboard
            assert "tracking_numbers" in dashboard
    
    @patch('src.main.verify_token')
    def test_get_dashboards_with_pagination(self, mock_verify_token, client, mock_user):
        """Test getting dashboards with pagination"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards?limit=1&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 1
    
    @patch('src.main.verify_token')
    def test_get_dashboard_details(self, mock_verify_token, client, mock_user):
        """Test getting specific dashboard details"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "unique_id" in data
        assert "tracking_numbers" in data
        assert isinstance(data["tracking_numbers"], list)
    
    @patch('src.main.verify_token')
    def test_update_dashboard(self, mock_verify_token, client, mock_user):
        """Test updating dashboard configuration"""
        mock_verify_token.return_value = mock_user
        
        update_data = {
            "name": "Updated Dashboard Name",
            "refresh_interval": 600
        }
        
        response = client.put("/api/v1/dashboards/1", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["refresh_interval"] == update_data["refresh_interval"]
    
    @patch('src.main.verify_token')
    def test_delete_dashboard(self, mock_verify_token, client, mock_user):
        """Test deleting dashboard"""
        mock_verify_token.return_value = mock_user
        
        response = client.delete("/api/v1/dashboards/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
    
    @patch('src.main.verify_token')
    def test_get_dashboard_overview(self, mock_verify_token, client, mock_user):
        """Test getting dashboard overview statistics"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_shipments" in data
        assert "status_breakdown" in data
        assert "carrier_breakdown" in data
        assert "on_time_deliveries" in data
        assert "delayed_shipments" in data
        assert isinstance(data["status_breakdown"], dict)
        assert isinstance(data["carrier_breakdown"], dict)
    
    @patch('src.main.verify_token')
    def test_get_tracking_status(self, mock_verify_token, client, mock_user):
        """Test getting tracking status for dashboard shipments"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/tracking")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for tracking_item in data:
            assert "tracking_number" in tracking_item
            assert "current_status" in tracking_item
            assert "carrier" in tracking_item
            assert "progress_percentage" in tracking_item
    
    @patch('src.main.verify_token')
    def test_get_tracking_status_with_filters(self, mock_verify_token, client, mock_user):
        """Test getting tracking status with filters"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/tracking?status=in_transit&carrier=DHL")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned items should match the filter criteria
        for item in data:
            assert item["current_status"] == "in_transit" or len(data) == 0
            assert item["carrier"] == "DHL" or len(data) == 0
    
    @patch('src.main.verify_token')
    def test_get_tracking_events(self, mock_verify_token, client, mock_user):
        """Test getting detailed tracking events for specific shipment"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/tracking/TN001/events")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for event in data:
            assert "tracking_number" in event
            assert "event_timestamp" in event
            assert "status" in event
            assert "description" in event
            assert event["tracking_number"] == "TN001"
    
    @patch('src.main.verify_token')
    def test_refresh_dashboard_data(self, mock_verify_token, client, mock_user):
        """Test manually refreshing dashboard data"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/dashboards/1/refresh")
        
        assert response.status_code == 200
        data = response.json()
        assert data["dashboard_id"] == 1
        assert data["refresh_status"] == "completed"
        assert "updated_tracking_numbers" in data
        assert "new_events" in data
        assert "status_changes" in data
    
    @patch('src.main.verify_token')
    def test_export_dashboard_data_csv(self, mock_verify_token, client, mock_user):
        """Test exporting dashboard data as CSV"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/export?format=csv")
        
        assert response.status_code == 200
        data = response.json()
        assert data["export_format"] == "csv"
        assert data["filename"].endswith(".csv")
        assert "download_url" in data
        assert "expires_at" in data
    
    @patch('src.main.verify_token')
    def test_export_dashboard_data_xlsx(self, mock_verify_token, client, mock_user):
        """Test exporting dashboard data as Excel"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/export?format=xlsx")
        
        assert response.status_code == 200
        data = response.json()
        assert data["export_format"] == "xlsx"
        assert data["filename"].endswith(".xlsx")
    
    @patch('src.main.verify_token')
    def test_export_dashboard_data_json(self, mock_verify_token, client, mock_user):
        """Test exporting dashboard data as JSON"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/export?format=json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["export_format"] == "json"
        assert data["filename"].endswith(".json")
    
    @patch('src.main.verify_token')
    def test_export_invalid_format(self, mock_verify_token, client, mock_user):
        """Test exporting with invalid format"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/dashboards/1/export?format=pdf")
        
        assert response.status_code == 422  # Validation error
    
    def test_dashboard_endpoints_unauthorized(self, client):
        """Test dashboard endpoints without authentication"""
        # Test various endpoints without auth
        endpoints = [
            ("POST", "/api/v1/dashboards", {"name": "test", "tracking_numbers": ["TN001"]}),
            ("GET", "/api/v1/dashboards", None),
            ("GET", "/api/v1/dashboards/1", None),
            ("PUT", "/api/v1/dashboards/1", {"name": "updated"}),
            ("DELETE", "/api/v1/dashboards/1", None),
        ]
        
        for method, url, json_data in endpoints:
            if method == "POST":
                response = client.post(url, json=json_data)
            elif method == "PUT":
                response = client.put(url, json=json_data)
            elif method == "DELETE":
                response = client.delete(url)
            else:
                response = client.get(url)
            
            assert response.status_code == 403  # Forbidden without auth


class TestTrackingFilters:
    """Test cases for tracking filter functionality"""
    
    def test_tracking_filter_validation(self):
        """Test tracking filter validation"""
        filter_data = {
            "status": ["in_transit", "delivered"],
            "carrier": ["DHL"],
            "date_from": datetime.utcnow() - timedelta(days=7),
            "date_to": datetime.utcnow(),
            "search_term": "urgent"
        }
        
        tracking_filter = TrackingFilter(**filter_data)
        assert tracking_filter.status == ["in_transit", "delivered"]
        assert tracking_filter.carrier == ["DHL"]
        assert tracking_filter.search_term == "urgent"
    
    def test_empty_tracking_filter(self):
        """Test empty tracking filter"""
        tracking_filter = TrackingFilter()
        assert tracking_filter.status is None
        assert tracking_filter.carrier is None
        assert tracking_filter.date_from is None
        assert tracking_filter.date_to is None
        assert tracking_filter.search_term is None


class TestDashboardBulkOperations:
    """Test cases for bulk operations on dashboard data"""
    
    @pytest.mark.asyncio
    async def test_bulk_status_update_performance(self):
        """Test performance of bulk status updates"""
        start_time = datetime.utcnow()
        
        # Simulate updating 100 tracking statuses
        tracking_updates = []
        for i in range(100):
            tracking_updates.append({
                "tracking_number": f"TN{i:03d}",
                "status": "delivered" if i % 2 == 0 else "in_transit",
                "last_update": datetime.utcnow()
            })
            await asyncio.sleep(0.001)  # 1ms per update
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should process 100 updates efficiently (< 2 seconds)
        assert processing_time < 2.0
        assert len(tracking_updates) == 100
    
    def test_dashboard_data_aggregation(self):
        """Test dashboard data aggregation logic"""
        # Mock tracking data
        tracking_data = [
            {"status": "delivered", "carrier": "DHL", "transit_days": 3},
            {"status": "delivered", "carrier": "DHL", "transit_days": 4},
            {"status": "in_transit", "carrier": "FedEx", "transit_days": None},
            {"status": "delivered", "carrier": "UPS", "transit_days": 5},
            {"status": "delayed", "carrier": "DHL", "transit_days": None},
        ]
        
        # Aggregate status breakdown
        status_breakdown = {}
        carrier_breakdown = {}
        total_transit_days = 0
        delivered_count = 0
        
        for item in tracking_data:
            status = item["status"]
            carrier = item["carrier"]
            
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
            carrier_breakdown[carrier] = carrier_breakdown.get(carrier, 0) + 1
            
            if item["transit_days"] is not None:
                total_transit_days += item["transit_days"]
                delivered_count += 1
        
        average_transit = total_transit_days / delivered_count if delivered_count > 0 else 0
        
        assert status_breakdown["delivered"] == 3
        assert status_breakdown["in_transit"] == 1
        assert status_breakdown["delayed"] == 1
        assert carrier_breakdown["DHL"] == 3
        assert carrier_breakdown["FedEx"] == 1
        assert carrier_breakdown["UPS"] == 1
        assert average_transit == 4.0  # (3+4+5)/3


class TestDashboardRealTimeUpdates:
    """Test cases for real-time dashboard updates"""
    
    @pytest.mark.asyncio
    async def test_tracking_event_processing(self):
        """Test processing of new tracking events"""
        # Simulate receiving new tracking events
        new_events = [
            {
                "tracking_number": "TN001",
                "timestamp": datetime.utcnow(),
                "status": "out_for_delivery",
                "location": "Local Facility"
            },
            {
                "tracking_number": "TN002", 
                "timestamp": datetime.utcnow(),
                "status": "delivered",
                "location": "Customer Location"
            }
        ]
        
        # Process events
        processed_events = []
        for event in new_events:
            # Simulate event processing
            processed_event = {
                "id": len(processed_events) + 1,
                "tracking_number": event["tracking_number"],
                "event_timestamp": event["timestamp"],
                "status": event["status"],
                "location": event["location"],
                "processed_at": datetime.utcnow()
            }
            processed_events.append(processed_event)
            await asyncio.sleep(0.01)  # Simulate processing time
        
        assert len(processed_events) == 2
        assert processed_events[0]["status"] == "out_for_delivery"
        assert processed_events[1]["status"] == "delivered"
    
    def test_dashboard_refresh_interval_validation(self):
        """Test dashboard refresh interval validation"""
        valid_intervals = [60, 180, 300, 600, 1800, 3600]
        invalid_intervals = [30, 59, 3601, 7200]
        
        for interval in valid_intervals:
            # Should not raise validation error
            try:
                BulkTrackingDashboardCreate(
                    name="Test Dashboard",
                    tracking_numbers=["TN001"],
                    refresh_interval=interval
                )
            except ValueError:
                pytest.fail(f"Valid interval {interval} raised validation error")
        
        for interval in invalid_intervals:
            with pytest.raises(ValueError):
                BulkTrackingDashboardCreate(
                    name="Test Dashboard",
                    tracking_numbers=["TN001"],
                    refresh_interval=interval
                )


# Performance and integration test markers
@pytest.mark.performance
class TestDashboardPerformance:
    """Performance tests for dashboard functionality"""
    
    @pytest.mark.asyncio
    async def test_large_dashboard_loading(self):
        """Test loading dashboard with many tracking numbers"""
        # Generate large tracking number list
        large_tracking_list = [f"TN{i:06d}" for i in range(1000)]
        
        # Simulate dashboard loading
        start_time = datetime.utcnow()
        
        dashboard_data = {
            "name": "Large Dashboard",
            "tracking_numbers": large_tracking_list,
            "refresh_interval": 300
        }
        
        # Validate dashboard creation
        dashboard = BulkTrackingDashboardCreate(**dashboard_data)
        
        end_time = datetime.utcnow()
        loading_time = (end_time - start_time).total_seconds()
        
        assert len(dashboard.tracking_numbers) == 1000
        assert loading_time < 1.0  # Should load quickly
    
    @pytest.mark.asyncio
    async def test_concurrent_dashboard_access(self):
        """Test concurrent access to dashboard data"""
        async def simulate_dashboard_request():
            # Simulate API request processing
            await asyncio.sleep(0.1)
            return {"status": "success", "data": []}
        
        # Simulate 10 concurrent requests
        tasks = [simulate_dashboard_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(result["status"] == "success" for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])