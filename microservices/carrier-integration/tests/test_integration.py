import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta

from src.main import app
from src.schemas import (
    QuoteRequest, LabelRequest, TrackingRequest,
    PickupRequest, Address, Package
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_carrier_service():
    with patch('src.main.app.state.carrier_service') as mock:
        yield mock


@pytest.fixture
def mock_exchange_service():
    with patch('src.main.app.state.exchange_rate_service') as mock:
        yield mock


class TestHealthEndpoints:
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'carrier-integration'
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert 'carrier_integration_requests_total' in response.text


class TestQuoteEndpoints:
    def test_get_quote_specific_carrier(self, client):
        """Test getting quote from specific carrier"""
        quote_request = {
            "carrier": "DHL",
            "origin": {
                "street": "123 Test St",
                "city": "Bogota",
                "postal_code": "110111",
                "country": "CO",
                "contact_name": "Test Sender",
                "contact_phone": "+573001234567"
            },
            "destination": {
                "street": "456 Main St",
                "city": "New York",
                "postal_code": "10001",
                "country": "US",
                "contact_name": "Test Receiver",
                "contact_phone": "+12125551234"
            },
            "packages": [{
                "weight_kg": 5.0,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15
            }]
        }
        
        with patch('src.main.app.state.carrier_service.get_quote') as mock_quote:
            mock_quote.return_value = AsyncMock(
                quote_id="TEST-123",
                carrier="DHL",
                service_type="Express",
                amount=150.00,
                currency="USD",
                estimated_days=3,
                valid_until=datetime.now() + timedelta(hours=24)
            )
            
            response = client.post("/api/v1/quotes", json=quote_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data['carrier'] == "DHL"
            assert data['amount'] == 150.00
    
    def test_get_best_quote(self, client):
        """Test getting best quote from all carriers"""
        quote_request = {
            # carrier not specified - get best quote
            "origin": {
                "street": "123 Test St",
                "city": "Bogota",
                "postal_code": "110111",
                "country": "CO",
                "contact_name": "Test Sender",
                "contact_phone": "+573001234567"
            },
            "destination": {
                "street": "456 Main St",
                "city": "Miami",
                "postal_code": "33101",
                "country": "US",
                "contact_name": "Test Receiver",
                "contact_phone": "+13055551234"
            },
            "packages": [{
                "weight_kg": 2.0,
                "length_cm": 20,
                "width_cm": 15,
                "height_cm": 10
            }]
        }
        
        with patch('src.main.app.state.carrier_service.get_best_quote') as mock_best:
            mock_best.return_value = AsyncMock(
                quote_id="BEST-123",
                carrier="FedEx",
                service_type="International Economy",
                amount=95.00,
                currency="USD",
                estimated_days=5,
                valid_until=datetime.now() + timedelta(hours=24)
            )
            
            response = client.post("/api/v1/quotes", json=quote_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data['carrier'] == "FedEx"
            assert data['amount'] == 95.00


class TestLabelEndpoints:
    def test_generate_label(self, client):
        """Test label generation"""
        label_request = {
            "carrier": "UPS",
            "order_id": "ORDER-001",
            "origin": {
                "street": "Calle 100 #15-20",
                "city": "Bogota",
                "postal_code": "110111",
                "country": "CO",
                "contact_name": "Test Sender",
                "contact_phone": "+573001234567"
            },
            "destination": {
                "street": "789 Oak Ave",
                "city": "Los Angeles",
                "postal_code": "90001",
                "country": "US",
                "contact_name": "Test Receiver",
                "contact_phone": "+12135551234"
            },
            "packages": [{
                "weight_kg": 3.0,
                "length_cm": 25,
                "width_cm": 20,
                "height_cm": 15,
                "declared_value": 200
            }],
            "service_type": "express"
        }
        
        with patch('src.main.app.state.carrier_service.generate_label') as mock_label:
            mock_label.return_value = AsyncMock(
                tracking_number="1Z999AA10123456784",
                carrier="UPS",
                label_data="base64_encoded_label",
                barcode="1Z999AA10123456784",
                estimated_delivery=datetime.now() + timedelta(days=3),
                cost=125.00,
                currency="USD"
            )
            
            response = client.post("/api/v1/labels", json=label_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data['tracking_number'] == "1Z999AA10123456784"
            assert data['carrier'] == "UPS"


class TestTrackingEndpoints:
    def test_track_shipment(self, client):
        """Test shipment tracking"""
        tracking_request = {
            "carrier": "DHL",
            "tracking_number": "DHL123456789"
        }
        
        with patch('src.main.app.state.carrier_service.track_shipment') as mock_track:
            mock_track.return_value = AsyncMock(
                tracking_number="DHL123456789",
                carrier="DHL",
                status="In Transit",
                current_location="Miami, FL",
                estimated_delivery=datetime.now() + timedelta(days=2),
                events=[
                    {
                        "date": datetime.now() - timedelta(days=1),
                        "status": "Picked Up",
                        "description": "Package picked up",
                        "location": "Bogota, CO"
                    },
                    {
                        "date": datetime.now(),
                        "status": "In Transit",
                        "description": "Package in transit",
                        "location": "Miami, FL"
                    }
                ]
            )
            
            response = client.post("/api/v1/tracking", json=tracking_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data['tracking_number'] == "DHL123456789"
            assert data['status'] == "In Transit"
            assert len(data['events']) == 2


class TestExchangeRateEndpoints:
    def test_get_current_trm(self, client):
        """Test getting current TRM"""
        with patch('src.main.app.state.exchange_rate_service.get_current_trm') as mock_trm:
            mock_trm.return_value = AsyncMock(
                rate=4250.50,
                from_currency="COP",
                to_currency="USD",
                valid_date=datetime.now(),
                source="banco_republica",
                spread=0.03,
                effective_rate=4378.02
            )
            
            response = client.get("/api/v1/exchange-rates/cop-usd")
            
            assert response.status_code == 200
            data = response.json()
            assert data['rate'] == 4250.50
            assert data['from_currency'] == "COP"
            assert data['to_currency'] == "USD"
            assert data['spread'] == 0.03
    
    def test_convert_currency(self, client):
        """Test currency conversion"""
        with patch('src.main.app.state.exchange_rate_service.convert') as mock_convert:
            mock_convert.return_value = 4250500.00
            
            with patch('src.main.app.state.exchange_rate_service.get_rate') as mock_rate:
                mock_rate.return_value = 4250.50
                
                response = client.post(
                    "/api/v1/exchange-rates/convert",
                    params={
                        "amount": 1000,
                        "from_currency": "USD",
                        "to_currency": "COP"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['original_amount'] == 1000
                assert data['from_currency'] == "USD"
                assert data['to_currency'] == "COP"
                assert data['converted_amount'] == 4250500.00


class TestCarrierCredentials:
    def test_save_carrier_credentials(self, client):
        """Test saving carrier credentials"""
        credentials_data = {
            "environment": "production",
            "credentials": {
                "username": "test_user",
                "password": "test_pass",
                "account_number": "ACC123"
            }
        }
        
        with patch('src.main.app.state.carrier_service.validate_credentials') as mock_validate:
            mock_validate.return_value = True
            
            with patch('src.main.app.state.carrier_service.save_credentials') as mock_save:
                mock_save.return_value = AsyncMock(
                    carrier="DHL",
                    environment="production",
                    is_active=True,
                    validated_at=datetime.now()
                )
                
                response = client.post(
                    "/api/v1/carriers/DHL/credentials",
                    json=credentials_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['carrier'] == "DHL"
                assert data['is_active'] is True


class TestFallbackConfiguration:
    def test_configure_fallback(self, client):
        """Test fallback configuration"""
        with patch('src.main.app.state.fallback_service.configure_priority') as mock_config:
            mock_config.return_value = None
            
            response = client.post(
                "/api/v1/fallback/configure",
                json={
                    "route": "CO-US",
                    "carriers": ["DHL", "FedEx", "UPS"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data['message'].lower()


class TestCarrierHealth:
    def test_get_carrier_health(self, client):
        """Test getting carrier health status"""
        with patch('src.main.app.state.carrier_service.get_health_status') as mock_health:
            mock_health.return_value = {
                "carrier": "DHL",
                "status": "operational",
                "latency_ms": 250.5,
                "error_rate": 0.01,
                "last_check": datetime.now(),
                "last_success": datetime.now(),
                "circuit_breaker_open": False
            }
            
            response = client.get("/api/v1/carriers/DHL/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['carrier'] == "DHL"
            assert data['status'] == "operational"
            assert data['circuit_breaker_open'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])