"""
Unit tests for SCRUM-13: Shipping Carrier Integrations (DHL, FedEx, UPS)
Tests cover carrier API integrations, rate calculation, shipment creation, tracking, and error handling
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.main import app
from src.integrations.factory import CarrierFactory, CARRIER_CONFIG_TEMPLATES
from src.integrations.base import ShippingRate, ShipmentRequest, ShipmentResponse, TrackingEvent, ShipmentStatus
from src.integrations.dhl import DHLIntegration
from src.integrations.fedex import FedExIntegration
from src.integrations.ups import UPSIntegration


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user with carrier permissions"""
    return {
        "user_id": "test_user_123",
        "company_id": "test_company_456",
        "permissions": ["admin:carriers", "shipping:create", "shipping:cancel"],
        "is_superuser": False
    }


@pytest.fixture
def sample_address():
    """Sample shipping address for testing"""
    return {
        "name": "John Doe",
        "company": "Test Company",
        "line1": "123 Main St",
        "city": "Miami",
        "state": "FL",
        "postal_code": "33101",
        "country_code": "US",
        "phone": "555-123-4567",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_shipment_request(sample_address):
    """Sample shipment request for testing"""
    return {
        "carrier_code": "DHL",
        "origin_address": {
            **sample_address,
            "city": "Mexico City",
            "state": "CDMX",  
            "postal_code": "06100",
            "country_code": "MX"
        },
        "destination_address": sample_address,
        "weight_kg": 2.5,
        "length_cm": 30,
        "width_cm": 20,
        "height_cm": 15,
        "value": 150.0,
        "currency": "USD",
        "description": "Electronics - Phone accessories",
        "reference_number": "REF123456"
    }


class TestCarrierFactory:
    """Test cases for carrier factory and configuration"""
    
    def test_get_supported_carriers(self):
        """Test getting list of supported carriers"""
        carriers = CarrierFactory.get_supported_carriers()
        assert "DHL" in carriers
        assert "FEDEX" in carriers
        assert "UPS" in carriers
        assert len(carriers) == 3
    
    def test_is_supported_carrier(self):
        """Test checking if carrier is supported"""
        assert CarrierFactory.is_supported("DHL")
        assert CarrierFactory.is_supported("dhl")  # Case insensitive
        assert CarrierFactory.is_supported("FEDEX")
        assert CarrierFactory.is_supported("UPS")
        assert not CarrierFactory.is_supported("USPS")
        assert not CarrierFactory.is_supported("invalid")
    
    def test_create_dhl_integration(self):
        """Test creating DHL integration"""
        config = {"api_key": "test_key", "api_secret": "test_secret"}
        integration = CarrierFactory.create_integration("DHL", config, sandbox=True)
        
        assert integration is not None
        assert isinstance(integration, DHLIntegration)
        assert integration.api_key == "test_key"
        assert integration.api_secret == "test_secret"
        assert integration.sandbox is True
    
    def test_create_fedex_integration(self):
        """Test creating FedEx integration"""
        config = {
            "api_key": "test_key", 
            "api_secret": "test_secret",
            "account_number": "123456789"
        }
        integration = CarrierFactory.create_integration("FEDEX", config, sandbox=True)
        
        assert integration is not None
        assert isinstance(integration, FedExIntegration)
        assert integration.api_key == "test_key"
        assert integration.account_number == "123456789"
    
    def test_create_ups_integration(self):
        """Test creating UPS integration"""
        config = {
            "api_key": "test_key",
            "user_id": "test_user", 
            "password": "test_pass",
            "account_number": "123456"
        }
        integration = CarrierFactory.create_integration("UPS", config, sandbox=True)
        
        assert integration is not None
        assert isinstance(integration, UPSIntegration)
        assert integration.api_key == "test_key"
        assert integration.user_id == "test_user"
        assert integration.account_number == "123456"
    
    def test_create_unsupported_carrier(self):
        """Test creating integration for unsupported carrier"""
        config = {"api_key": "test_key"}
        integration = CarrierFactory.create_integration("USPS", config)
        
        assert integration is None
    
    def test_config_templates(self):
        """Test carrier configuration templates"""
        assert "DHL" in CARRIER_CONFIG_TEMPLATES
        assert "FEDEX" in CARRIER_CONFIG_TEMPLATES
        assert "UPS" in CARRIER_CONFIG_TEMPLATES
        
        dhl_template = CARRIER_CONFIG_TEMPLATES["DHL"]
        assert "api_key" in dhl_template["required_fields"]
        assert "api_secret" in dhl_template["required_fields"]


class TestDHLIntegration:
    """Test cases for DHL integration"""
    
    @pytest.fixture
    def dhl_integration(self):
        """DHL integration fixture"""
        return DHLIntegration("test_key", "test_secret", sandbox=True)
    
    def test_dhl_base_url(self, dhl_integration):
        """Test DHL base URL configuration"""
        assert "test" in dhl_integration.base_url
        
        # Test production URL
        prod_integration = DHLIntegration("key", "secret", sandbox=False)
        assert "test" not in prod_integration.base_url
    
    def test_dhl_headers(self, dhl_integration):
        """Test DHL API headers"""
        headers = dhl_integration._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    def test_dhl_status_normalization(self, dhl_integration):
        """Test DHL status normalization"""
        assert dhl_integration._normalize_status("DELIVERED") == ShipmentStatus.DELIVERED
        assert dhl_integration._normalize_status("PROCESSED AT") == ShipmentStatus.IN_TRANSIT
        assert dhl_integration._normalize_status("WITH DELIVERY COURIER") == ShipmentStatus.OUT_FOR_DELIVERY
        assert dhl_integration._normalize_status("SHIPMENT ON HOLD") == ShipmentStatus.EXCEPTION
        assert dhl_integration._normalize_status("UNKNOWN STATUS") == ShipmentStatus.IN_TRANSIT
    
    @pytest.mark.asyncio
    async def test_dhl_calculate_rates(self, dhl_integration):
        """Test DHL rate calculation"""
        rates = await dhl_integration.calculate_rates(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        assert len(rates) > 0
        assert all(isinstance(rate, ShippingRate) for rate in rates)
        assert all(rate.carrier == "DHL Express" for rate in rates)
        assert all(rate.total_cost > 0 for rate in rates)
        assert all(rate.transit_days > 0 for rate in rates)
    
    @pytest.mark.asyncio
    async def test_dhl_create_shipment(self, dhl_integration, sample_address):
        """Test DHL shipment creation"""
        request = ShipmentRequest(
            origin_address={**sample_address, "country_code": "MX"},
            destination_address=sample_address,
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0,
            currency="USD",
            description="Test shipment"
        )
        
        response = await dhl_integration.create_shipment(request)
        
        assert isinstance(response, ShipmentResponse)
        assert response.carrier == "DHL Express"
        assert response.tracking_number.startswith("DHL")
        assert response.total_cost > 0
        assert response.label_url
        assert response.label_format == "PDF"
    
    @pytest.mark.asyncio
    async def test_dhl_track_shipment(self, dhl_integration):
        """Test DHL shipment tracking"""
        tracking_data = await dhl_integration.track_shipment("DHL1234567890")
        
        assert tracking_data["tracking_number"] == "DHL1234567890"
        assert tracking_data["carrier"] == "DHL Express"
        assert "events" in tracking_data
        assert len(tracking_data["events"]) > 0
        assert "status" in tracking_data
        assert "estimated_delivery" in tracking_data
    
    @pytest.mark.asyncio
    async def test_dhl_cancel_shipment(self, dhl_integration):
        """Test DHL shipment cancellation"""
        # Mock implementation returns True for demonstration
        success = await dhl_integration.cancel_shipment("DHL1234567890")
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_dhl_validate_address(self, dhl_integration, sample_address):
        """Test DHL address validation"""
        result = await dhl_integration.validate_address(sample_address)
        
        assert "valid" in result
        assert "normalized_address" in result
        assert isinstance(result["valid"], bool)


class TestFedExIntegration:
    """Test cases for FedEx integration"""
    
    @pytest.fixture
    def fedex_integration(self):
        """FedEx integration fixture"""
        return FedExIntegration("test_key", "test_secret", "123456789", sandbox=True)
    
    def test_fedex_base_url(self, fedex_integration):
        """Test FedEx base URL configuration"""
        assert "sandbox" in fedex_integration.base_url
        
        # Test production URL
        prod_integration = FedExIntegration("key", "secret", "123", sandbox=False)
        assert "sandbox" not in prod_integration.base_url
    
    def test_fedex_status_normalization(self, fedex_integration):
        """Test FedEx status normalization"""
        assert fedex_integration._normalize_status("DELIVERED") == ShipmentStatus.DELIVERED
        assert fedex_integration._normalize_status("IN_TRANSIT") == ShipmentStatus.IN_TRANSIT
        assert fedex_integration._normalize_status("OUT_FOR_DELIVERY") == ShipmentStatus.OUT_FOR_DELIVERY
        assert fedex_integration._normalize_status("PICKED_UP") == ShipmentStatus.PICKED_UP
        assert fedex_integration._normalize_status("UNKNOWN") == ShipmentStatus.IN_TRANSIT
    
    @pytest.mark.asyncio
    async def test_fedex_calculate_rates(self, fedex_integration):
        """Test FedEx rate calculation"""
        rates = await fedex_integration.calculate_rates(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        assert len(rates) > 0
        assert all(isinstance(rate, ShippingRate) for rate in rates)
        assert all(rate.carrier == "FedEx" for rate in rates)
        assert all(rate.total_cost > 0 for rate in rates)
    
    @pytest.mark.asyncio
    async def test_fedex_create_shipment(self, fedex_integration, sample_address):
        """Test FedEx shipment creation"""
        request = ShipmentRequest(
            origin_address={**sample_address, "country_code": "MX"},
            destination_address=sample_address,
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0,
            currency="USD",
            description="Test shipment"
        )
        
        response = await fedex_integration.create_shipment(request)
        
        assert isinstance(response, ShipmentResponse)
        assert response.carrier == "FedEx"
        assert response.tracking_number.startswith("FX")
        assert response.total_cost > 0


class TestUPSIntegration:
    """Test cases for UPS integration"""
    
    @pytest.fixture
    def ups_integration(self):
        """UPS integration fixture"""
        return UPSIntegration("test_key", "test_user", "test_pass", "123456", sandbox=True)
    
    def test_ups_base_url(self, ups_integration):
        """Test UPS base URL configuration"""
        assert "wwwcie" in ups_integration.base_url
        
        # Test production URL
        prod_integration = UPSIntegration("key", "user", "pass", "123", sandbox=False)
        assert "wwwcie" not in prod_integration.base_url
    
    def test_ups_service_names(self, ups_integration):
        """Test UPS service name mapping"""
        assert ups_integration._get_service_name("07") == "UPS Worldwide Express"
        assert ups_integration._get_service_name("08") == "UPS Worldwide Expedited"
        assert ups_integration._get_service_name("11") == "UPS Standard"
        assert ups_integration._get_service_name("99") == "UPS Express"  # Default
    
    def test_ups_status_normalization(self, ups_integration):
        """Test UPS status normalization"""
        assert ups_integration._normalize_status("D") == ShipmentStatus.DELIVERED
        assert ups_integration._normalize_status("I") == ShipmentStatus.IN_TRANSIT
        assert ups_integration._normalize_status("O") == ShipmentStatus.OUT_FOR_DELIVERY
        assert ups_integration._normalize_status("P") == ShipmentStatus.PICKED_UP
        assert ups_integration._normalize_status("X") == ShipmentStatus.EXCEPTION
    
    @pytest.mark.asyncio
    async def test_ups_calculate_rates(self, ups_integration):
        """Test UPS rate calculation"""
        rates = await ups_integration.calculate_rates(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        assert len(rates) > 0
        assert all(isinstance(rate, ShippingRate) for rate in rates)
        assert all(rate.carrier == "UPS" for rate in rates)
        assert all(rate.total_cost > 0 for rate in rates)


class TestCarrierIntegrationEndpoints:
    """Test cases for carrier integration API endpoints"""
    
    @patch('src.main.verify_token')
    def test_get_carrier_templates(self, mock_verify_token, client, mock_user):
        """Test getting carrier configuration templates"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/carriers/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_carriers" in data
        assert "templates" in data
        assert "DHL" in data["supported_carriers"]
        assert "FEDEX" in data["supported_carriers"]
        assert "UPS" in data["supported_carriers"]
    
    @patch('src.main.verify_token')
    def test_configure_carrier(self, mock_verify_token, client, mock_user):
        """Test configuring carrier credentials"""
        mock_verify_token.return_value = mock_user
        
        config_data = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "sandbox": True
        }
        
        response = client.post("/api/v1/carriers/DHL/configure", json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["carrier_code"] == "DHL"
        assert data["configured"] is True
        assert data["sandbox"] is True
    
    @patch('src.main.verify_token')
    def test_configure_unsupported_carrier(self, mock_verify_token, client, mock_user):
        """Test configuring unsupported carrier"""
        mock_verify_token.return_value = mock_user
        
        config_data = {"api_key": "test_key"}
        
        response = client.post("/api/v1/carriers/USPS/configure", json=config_data)
        
        assert response.status_code == 400
        assert "Unsupported carrier" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_calculate_shipping_rates(self, mock_verify_token, client, mock_user):
        """Test calculating shipping rates from multiple carriers"""
        mock_verify_token.return_value = mock_user
        
        rate_request = {
            "origin_country": "MX",
            "destination_country": "US",
            "weight_kg": 2.5,
            "length_cm": 30,
            "width_cm": 20,
            "height_cm": 15,
            "value": 150.0,
            "currency": "USD"
        }
        
        response = client.post("/api/v1/shipping/rates/calculate", json=rate_request)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check that rates from multiple carriers are returned
        carriers = {rate["carrier"] for rate in data}
        assert len(carriers) > 1  # Multiple carriers
        
        # Check rate structure
        for rate in data:
            assert "carrier" in rate
            assert "service_type" in rate
            assert "total_cost" in rate
            assert "transit_days" in rate
            assert rate["total_cost"] > 0
    
    @patch('src.main.verify_token')
    def test_calculate_rates_specific_carriers(self, mock_verify_token, client, mock_user):
        """Test calculating rates for specific carriers only"""
        mock_verify_token.return_value = mock_user
        
        rate_request = {
            "origin_country": "MX",
            "destination_country": "US",
            "weight_kg": 2.5,
            "length_cm": 30,
            "width_cm": 20,
            "height_cm": 15,
            "value": 150.0,
            "carrier_codes": ["DHL", "FEDEX"]
        }
        
        response = client.post("/api/v1/shipping/rates/calculate", json=rate_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only have DHL and FedEx rates
        carriers = {rate["carrier"] for rate in data}
        assert "DHL Express" in carriers or "DHL" in [rate["carrier"] for rate in data]
        assert "FedEx" in carriers or "FedEx" in [rate["carrier"] for rate in data]
        assert "UPS" not in carriers
    
    @patch('src.main.verify_token')
    def test_create_shipment(self, mock_verify_token, client, mock_user, sample_shipment_request):
        """Test creating shipment with carrier"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/shipping/shipments", json=sample_shipment_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "tracking_number" in data
        assert data["carrier"] == "DHL Express"
        assert "label_url" in data
        assert "estimated_delivery" in data
        assert data["total_cost"] > 0
    
    @patch('src.main.verify_token')
    def test_create_shipment_unsupported_carrier(self, mock_verify_token, client, mock_user, sample_shipment_request):
        """Test creating shipment with unsupported carrier"""
        mock_verify_token.return_value = mock_user
        
        sample_shipment_request["carrier_code"] = "USPS"
        
        response = client.post("/api/v1/shipping/shipments", json=sample_shipment_request)
        
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_track_shipment_external(self, mock_verify_token, client, mock_user):
        """Test tracking shipment using external carrier APIs"""
        mock_verify_token.return_value = mock_user
        
        # Test with DHL tracking number
        response = client.get("/api/v1/shipping/track/DHL1234567890")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_number"] == "DHL1234567890"
        assert "carrier" in data
        assert "events" in data
        assert "status" in data
    
    @patch('src.main.verify_token')
    def test_track_shipment_with_carrier_code(self, mock_verify_token, client, mock_user):
        """Test tracking shipment with explicit carrier code"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/shipping/track/1234567890?carrier_code=FEDEX")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_number"] == "1234567890"
        assert data["carrier"] == "FedEx"
    
    @patch('src.main.verify_token')
    def test_cancel_shipment_external(self, mock_verify_token, client, mock_user):
        """Test cancelling shipment using external carrier API"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/shipping/shipments/DHL1234567890/cancel?carrier_code=DHL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_number"] == "DHL1234567890"
        assert data["carrier"] == "DHL"
        assert "cancelled" in data
        assert "message" in data
    
    @patch('src.main.verify_token')
    def test_validate_shipping_address(self, mock_verify_token, client, mock_user, sample_address):
        """Test validating shipping address"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/shipping/validate-address?carrier_code=UPS", json=sample_address)
        
        assert response.status_code == 200
        data = response.json()
        assert data["carrier"] == "UPS"
        assert "original_address" in data
        assert "validation_result" in data
        assert "validated_at" in data
    
    def test_carrier_endpoints_unauthorized(self, client):
        """Test carrier endpoints without authentication"""
        endpoints = [
            ("GET", "/api/v1/carriers/templates", None),
            ("POST", "/api/v1/carriers/DHL/configure", {"api_key": "test"}),
            ("POST", "/api/v1/shipping/rates/calculate", {"origin_country": "US"}),
        ]
        
        for method, url, json_data in endpoints:
            if method == "POST":
                response = client.post(url, json=json_data)
            else:
                response = client.get(url)
            
            assert response.status_code == 403  # Forbidden without auth


class TestCarrierIntegrationErrorHandling:
    """Test cases for error handling in carrier integrations"""
    
    @pytest.mark.asyncio
    async def test_invalid_carrier_config(self):
        """Test error handling with invalid carrier configuration"""
        # Missing required fields
        integration = CarrierFactory.create_integration("DHL", {}, sandbox=True)
        assert integration.api_key == ""
        assert integration.api_secret == ""
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """Test handling of API timeouts"""
        integration = DHLIntegration("test_key", "test_secret", sandbox=True)
        
        # The mock implementation should handle timeouts gracefully
        rates = await integration.calculate_rates("MX", "US", 2.5, 30, 20, 15, 150.0)
        assert len(rates) > 0  # Should return mock data on API failure
    
    @pytest.mark.asyncio
    async def test_invalid_tracking_number_format(self):
        """Test handling of invalid tracking number formats"""
        integration = UPSIntegration("test_key", "user", "pass", "123456", sandbox=True)
        
        # Should still return mock data even with invalid format
        tracking_data = await integration.track_shipment("INVALID123")
        assert "tracking_number" in tracking_data
        assert tracking_data["tracking_number"] == "INVALID123"


# Performance test markers
@pytest.mark.performance
class TestCarrierIntegrationPerformance:
    """Performance tests for carrier integrations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_requests(self):
        """Test concurrent rate requests to multiple carriers"""
        configs = {
            "DHL": {"api_key": "test", "api_secret": "test"},
            "FEDEX": {"api_key": "test", "api_secret": "test", "account_number": "123"},
            "UPS": {"api_key": "test", "user_id": "test", "password": "test", "account_number": "123"}
        }
        
        async def get_rates(carrier_code, config):
            integration = CarrierFactory.create_integration(carrier_code, config, sandbox=True)
            return await integration.calculate_rates("MX", "US", 2.5, 30, 20, 15, 150.0)
        
        # Execute rate requests concurrently
        tasks = [get_rates(code, config) for code, config in configs.items()]
        start_time = datetime.utcnow()
        results = await asyncio.gather(*tasks)
        end_time = datetime.utcnow()
        
        # Should complete within reasonable time
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 5.0  # Less than 5 seconds for 3 concurrent requests
        
        # All should return results
        assert len(results) == 3
        assert all(len(rates) > 0 for rates in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])