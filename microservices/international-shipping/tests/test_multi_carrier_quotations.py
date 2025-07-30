"""
Unit tests for SCRUM-39: Multi-Carrier Quotation System
Tests cover DHL, FedEx, UPS quotation comparison, cost analysis, and recommendation engine
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.main import app
from src.quotation.multi_carrier import (
    MultiCarrierQuotationService, QuotationRequest, QuotationResponse, 
    CarrierQuote
)


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "user_id": "test_user_123",
        "company_id": "test_company_456",
        "permissions": ["shipping:quote", "shipping:compare"],
        "is_superuser": False
    }


@pytest.fixture
def sample_quotation_request():
    """Sample quotation request for testing"""
    return QuotationRequest(
        origin_country="MX",
        destination_country="US",
        origin_city="Mexico City",
        destination_city="Miami",
        weight_kg=2.5,
        length_cm=30,
        width_cm=20,
        height_cm=15,
        value=150.0,
        currency="USD"
    )


@pytest.fixture
def sample_carrier_quotes():
    """Sample carrier quotes for testing"""
    return [
        CarrierQuote(
            carrier_code="DHL",
            carrier_name="DHL Express",
            service_type="Express Worldwide",
            base_rate=42.0,
            weight_rate=16.25,
            fuel_surcharge=6.99,
            insurance_rate=0.75,
            total_cost=65.99,
            currency="USD",
            transit_days=3,
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            cutoff_time="18:00",
            confidence_score=0.95,
            valid_until=datetime.utcnow() + timedelta(hours=24)
        ),
        CarrierQuote(
            carrier_code="FEDEX",
            carrier_name="FedEx",
            service_type="International Priority",
            base_rate=38.5,
            weight_rate=16.25,
            fuel_surcharge=5.48,
            insurance_rate=0.60,
            total_cost=60.83,
            currency="USD",
            transit_days=3,
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            cutoff_time="19:00",
            confidence_score=0.93,
            valid_until=datetime.utcnow() + timedelta(hours=24)
        ),
        CarrierQuote(
            carrier_code="UPS",
            carrier_name="UPS",
            service_type="Worldwide Express",
            base_rate=40.25,
            weight_rate=16.25,
            fuel_surcharge=6.76,
            insurance_rate=0.75,
            total_cost=64.01,
            currency="USD",
            transit_days=3,
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            cutoff_time="17:30",
            confidence_score=0.92,
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )
    ]


@pytest.fixture
def quotation_service():
    """MultiCarrierQuotationService fixture"""
    service = MultiCarrierQuotationService()
    
    # Mock carrier factory
    class MockCarrierFactory:
        @staticmethod
        def create_integration(carrier_code, config, sandbox=True):
            class MockIntegration:
                def __init__(self, carrier_code):
                    self.carrier_code = carrier_code
                
                async def calculate_rates(self, *args, **kwargs):
                    from src.integrations.base import ShippingRate
                    
                    # Mock rates based on carrier
                    mock_rates = {
                        "DHL": [
                            ShippingRate(
                                carrier="DHL Express",
                                service_type="Express Worldwide",
                                base_rate=42.0,
                                weight_rate=16.25,
                                fuel_surcharge=6.99,
                                insurance_rate=0.75,
                                total_cost=65.99,
                                currency="USD",
                                transit_days=3,
                                valid_until=datetime.utcnow() + timedelta(hours=24)
                            )
                        ],
                        "FEDEX": [
                            ShippingRate(
                                carrier="FedEx",
                                service_type="International Priority",
                                base_rate=38.5,
                                weight_rate=16.25,
                                fuel_surcharge=5.48,
                                insurance_rate=0.60,
                                total_cost=60.83,
                                currency="USD",
                                transit_days=3,
                                valid_until=datetime.utcnow() + timedelta(hours=24)
                            )
                        ],
                        "UPS": [
                            ShippingRate(
                                carrier="UPS",
                                service_type="Worldwide Express",
                                base_rate=40.25,
                                weight_rate=16.25,
                                fuel_surcharge=6.76,
                                insurance_rate=0.75,
                                total_cost=64.01,
                                currency="USD",
                                transit_days=3,
                                valid_until=datetime.utcnow() + timedelta(hours=24)
                            )
                        ]
                    }
                    
                    return mock_rates.get(carrier_code, [])
            
            return MockIntegration(carrier_code) if carrier_code in ["DHL", "FEDEX", "UPS"] else None
    
    service.set_carrier_factory(MockCarrierFactory())
    
    # Set carrier configs
    configs = {
        "DHL": {"api_key": "test_dhl", "api_secret": "test_secret"},
        "FEDEX": {"api_key": "test_fedex", "api_secret": "test_secret", "account_number": "123"},
        "UPS": {"api_key": "test_ups", "user_id": "test_user", "password": "test_pass", "account_number": "456"}
    }
    
    for carrier, config in configs.items():
        service.set_carrier_config(carrier, config)
    
    return service


class TestQuotationRequest:
    """Test cases for QuotationRequest model"""
    
    def test_quotation_request_creation(self):
        """Test creating a quotation request"""
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        assert request.origin_country == "MX"
        assert request.destination_country == "US"
        assert request.weight_kg == 2.5
        assert request.value == 150.0
        assert request.currency == "USD"  # Default value
    
    def test_quotation_request_with_filters(self):
        """Test quotation request with carrier and service filters"""
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0,
            carrier_codes=["DHL", "FEDEX"],
            service_types=["Express", "Priority"]
        )
        
        assert request.carrier_codes == ["DHL", "FEDEX"]
        assert request.service_types == ["Express", "Priority"]


class TestCarrierQuote:
    """Test cases for CarrierQuote model"""
    
    def test_carrier_quote_creation(self, sample_carrier_quotes):
        """Test creating carrier quote objects"""
        quote = sample_carrier_quotes[0]  # DHL quote
        
        assert quote.carrier_code == "DHL"
        assert quote.carrier_name == "DHL Express"
        assert quote.service_type == "Express Worldwide"
        assert quote.total_cost == 65.99
        assert quote.transit_days == 3
        assert quote.available is True
        assert quote.confidence_score == 0.95
    
    def test_carrier_quote_cost_breakdown(self, sample_carrier_quotes):
        """Test carrier quote cost breakdown"""
        quote = sample_carrier_quotes[1]  # FedEx quote
        
        # Verify cost components add up correctly
        expected_total = (
            quote.base_rate + 
            quote.weight_rate + 
            quote.fuel_surcharge + 
            quote.insurance_rate
        )
        
        assert abs(quote.total_cost - expected_total) < 0.01
    
    def test_carrier_quote_availability(self):
        """Test carrier quote availability handling"""
        # Available quote
        available_quote = CarrierQuote(
            carrier_code="DHL",
            carrier_name="DHL Express",
            service_type="Express Worldwide",
            base_rate=42.0,
            total_cost=65.99,
            transit_days=3,
            available=True,
            confidence_score=0.95,
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert available_quote.available is True
        assert available_quote.error_message is None
        
        # Unavailable quote
        unavailable_quote = CarrierQuote(
            carrier_code="UPS",
            carrier_name="UPS",
            service_type="Service Unavailable",
            base_rate=0.0,
            total_cost=0.0,
            transit_days=0,
            available=False,
            confidence_score=0.0,
            error_message="API timeout",
            valid_until=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert unavailable_quote.available is False
        assert unavailable_quote.error_message == "API timeout"


class TestMultiCarrierQuotationService:
    """Test cases for MultiCarrierQuotationService"""
    
    @pytest.mark.asyncio
    async def test_get_quotations_all_carriers(self, quotation_service, sample_quotation_request):
        """Test getting quotations from all carriers"""
        response = await quotation_service.get_quotations(sample_quotation_request)
        
        assert isinstance(response, QuotationResponse)
        assert len(response.quotes) == 3  # DHL, FedEx, UPS
        assert response.successful_carriers == 3
        assert response.total_quotes == 3
        
        # Check that we have quotes from all expected carriers
        carrier_codes = {quote.carrier_code for quote in response.quotes}
        assert carrier_codes == {"DHL", "FEDEX", "UPS"}
    
    @pytest.mark.asyncio
    async def test_get_quotations_specific_carriers(self, quotation_service):
        """Test getting quotations from specific carriers only"""
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0,
            carrier_codes=["DHL", "FEDEX"]  # Only DHL and FedEx
        )
        
        response = await quotation_service.get_quotations(request)
        
        assert len(response.quotes) == 2
        carrier_codes = {quote.carrier_code for quote in response.quotes}
        assert carrier_codes == {"DHL", "FEDEX"}
        assert "UPS" not in carrier_codes
    
    @pytest.mark.asyncio
    async def test_get_quotations_with_service_filter(self, quotation_service):
        """Test getting quotations with service type filter"""
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0,
            service_types=["Express Worldwide"]  # Only this service type
        )
        
        response = await quotation_service.get_quotations(request)
        
        # Should only return quotes matching the service type filter
        for quote in response.quotes:
            assert "Express" in quote.service_type or "Worldwide" in quote.service_type
    
    @pytest.mark.asyncio
    async def test_best_options_identification(self, quotation_service, sample_quotation_request):
        """Test identification of cheapest, fastest, and recommended quotes"""
        response = await quotation_service.get_quotations(sample_quotation_request)
        
        # Should have identified best options
        assert response.cheapest_quote is not None
        assert response.fastest_quote is not None
        assert response.recommended_quote is not None
        
        # Cheapest should have lowest cost
        costs = [quote.total_cost for quote in response.quotes if quote.available]
        assert response.cheapest_quote.total_cost == min(costs)
        
        # Fastest should have lowest transit days
        transit_days = [quote.transit_days for quote in response.quotes if quote.available]
        assert response.fastest_quote.transit_days == min(transit_days)
    
    def test_calculate_recommended_quote(self, quotation_service, sample_carrier_quotes):
        """Test recommended quote calculation algorithm"""
        recommended = quotation_service._calculate_recommended_quote(sample_carrier_quotes)
        
        assert recommended is not None
        assert recommended in sample_carrier_quotes
        
        # Should be one of the available quotes
        assert recommended.available is True
    
    def test_calculate_recommended_quote_empty_list(self, quotation_service):
        """Test recommended quote calculation with empty list"""
        recommended = quotation_service._calculate_recommended_quote([])
        assert recommended is None
    
    def test_calculate_recommended_quote_no_available(self, quotation_service):
        """Test recommended quote calculation with no available quotes"""
        unavailable_quotes = [
            CarrierQuote(
                carrier_code="DHL",
                carrier_name="DHL Express",
                service_type="Service Unavailable",
                base_rate=0.0,
                total_cost=0.0,
                transit_days=0,
                available=False,
                confidence_score=0.0,
                valid_until=datetime.utcnow() + timedelta(hours=1)
            )
        ]
        
        recommended = quotation_service._calculate_recommended_quote(unavailable_quotes)
        assert recommended is None
    
    def test_get_carrier_display_name(self, quotation_service):
        """Test carrier display name mapping"""
        assert quotation_service._get_carrier_display_name("DHL") == "DHL Express"
        assert quotation_service._get_carrier_display_name("FEDEX") == "FedEx"
        assert quotation_service._get_carrier_display_name("UPS") == "UPS"
        assert quotation_service._get_carrier_display_name("UNKNOWN") == "UNKNOWN"
    
    def test_get_carrier_cutoff_time(self, quotation_service):
        """Test carrier cutoff time mapping"""
        assert quotation_service._get_carrier_cutoff_time("DHL") == "18:00"
        assert quotation_service._get_carrier_cutoff_time("FEDEX") == "19:00"
        assert quotation_service._get_carrier_cutoff_time("UPS") == "17:30"
        assert quotation_service._get_carrier_cutoff_time("UNKNOWN") == "17:00"
    
    def test_calculate_confidence_score(self, quotation_service):
        """Test confidence score calculation"""
        # Test base scores
        assert quotation_service._calculate_confidence_score("DHL", "Standard") == 0.95
        assert quotation_service._calculate_confidence_score("FEDEX", "Standard") == 0.93
        assert quotation_service._calculate_confidence_score("UPS", "Standard") == 0.92
        
        # Test service modifiers
        dhl_express = quotation_service._calculate_confidence_score("DHL", "Express Worldwide")
        assert dhl_express > 0.95  # Should be higher due to Express modifier
        
        fedex_economy = quotation_service._calculate_confidence_score("FEDEX", "Economy Service")
        assert fedex_economy < 0.93  # Should be lower due to Economy modifier
    
    @pytest.mark.asyncio
    async def test_get_carrier_quote_comparison(self, quotation_service, sample_quotation_request):
        """Test detailed carrier comparison analysis"""
        comparison = await quotation_service.get_carrier_quote_comparison(sample_quotation_request)
        
        assert "quotation_summary" in comparison
        assert "cost_analysis" in comparison
        assert "time_analysis" in comparison
        assert "carrier_breakdown" in comparison
        assert "recommendations" in comparison
        
        # Check cost analysis structure
        cost_analysis = comparison["cost_analysis"]
        assert "min_cost" in cost_analysis
        assert "max_cost" in cost_analysis
        assert "avg_cost" in cost_analysis
        assert "cost_spread" in cost_analysis
        
        # Check time analysis structure
        time_analysis = comparison["time_analysis"]
        assert "fastest_delivery" in time_analysis
        assert "slowest_delivery" in time_analysis
        assert "avg_delivery" in time_analysis
        
        # Check carrier breakdown
        carrier_breakdown = comparison["carrier_breakdown"]
        assert len(carrier_breakdown) > 0
        
        # Check recommendations
        recommendations = comparison["recommendations"]
        assert len(recommendations) > 0
        assert all("type" in rec and "message" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, quotation_service):
        """Test quotation timeout handling"""
        # Set very short timeout for testing
        quotation_service.quotation_timeout = 0.001  # 1ms
        
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        # Mock slow carrier integration
        class SlowMockFactory:
            @staticmethod
            def create_integration(carrier_code, config, sandbox=True):
                class SlowIntegration:
                    async def calculate_rates(self, *args, **kwargs):
                        await asyncio.sleep(1)  # Simulate slow API
                        return []
                
                return SlowIntegration()
        
        quotation_service.set_carrier_factory(SlowMockFactory())
        
        response = await quotation_service.get_quotations(request)
        
        # Should handle timeout gracefully
        assert len(response.errors) > 0
        assert any("timeout" in error["error"].lower() for error in response.errors)


class TestQuotationEndpoints:
    """Test cases for quotation API endpoints"""
    
    @patch('src.main.verify_token')
    def test_multi_carrier_quotation_endpoint(self, mock_verify_token, client, mock_user):
        """Test multi-carrier quotation endpoint"""
        mock_verify_token.return_value = mock_user
        
        response = client.post(
            "/api/v1/quotations/multi-carrier",
            params={
                "origin_country": "MX",
                "destination_country": "US",
                "weight_kg": 2.5,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15,
                "value": 150.0,
                "origin_city": "Mexico City",
                "destination_city": "Miami"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "request_id" in data
        assert "quotes" in data
        assert "cheapest_quote" in data
        assert "fastest_quote" in data
        assert "recommended_quote" in data
        assert "total_quotes" in data
        assert "processing_time_ms" in data
    
    @patch('src.main.verify_token')
    def test_multi_carrier_quotation_with_filters(self, mock_verify_token, client, mock_user):
        """Test multi-carrier quotation with carrier and service filters"""
        mock_verify_token.return_value = mock_user
        
        response = client.post(
            "/api/v1/quotations/multi-carrier",
            params={
                "origin_country": "MX",
                "destination_country": "US",
                "weight_kg": 2.5,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15,
                "value": 150.0,
                "carriers": "DHL,FEDEX",  # Only these carriers
                "services": "Express"     # Only Express services
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only have quotes from specified carriers
        quotes = data["quotes"]
        carrier_codes = {quote["carrier_code"] for quote in quotes}
        
        # May have both or just one depending on which services match filter
        assert carrier_codes.issubset({"DHL", "FEDEX"})
        assert "UPS" not in carrier_codes
    
    @patch('src.main.verify_token')
    def test_quotation_comparison_endpoint(self, mock_verify_token, client, mock_user):
        """Test quotation comparison endpoint"""
        mock_verify_token.return_value = mock_user
        
        response = client.post(
            "/api/v1/quotations/comparison",
            params={
                "origin_country": "MX",
                "destination_country": "US",
                "weight_kg": 2.5,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15,
                "value": 150.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "quotation_summary" in data
        assert "cost_analysis" in data
        assert "time_analysis" in data
        assert "carrier_breakdown" in data
        assert "recommendations" in data
        assert "quotes" in data
    
    @patch('src.main.verify_token')
    def test_get_available_carriers_endpoint(self, mock_verify_token, client, mock_user):
        """Test get available carriers endpoint"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/quotations/carriers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "carriers" in data
        assert "total_carriers" in data
        assert "supported_countries" in data
        assert "quotation_features" in data
        
        # Check carrier structure
        carriers = data["carriers"]
        assert "DHL" in carriers
        assert "FEDEX" in carriers
        assert "UPS" in carriers
        
        # Each carrier should have required fields
        for carrier_code, carrier_info in carriers.items():
            assert "name" in carrier_info
            assert "code" in carrier_info
            assert "services" in carrier_info
            assert "countries" in carrier_info
            assert "features" in carrier_info
    
    @patch('src.main.verify_token')
    def test_get_supported_countries_endpoint(self, mock_verify_token, client, mock_user):
        """Test get supported countries endpoint"""
        mock_verify_token.return_value = mock_user
        
        response = client.get("/api/v1/quotations/countries")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "countries" in data
        assert "regions" in data
        assert "total_countries" in data
        assert "shipping_zones" in data
        
        # Check country structure
        countries = data["countries"]
        assert "MX" in countries
        assert "US" in countries
        
        # Each country should have required fields
        for country_code, country_info in countries.items():
            assert "name" in country_info
            assert "region" in country_info
            assert "zone" in country_info
        
        # Check regions structure
        regions = data["regions"]
        assert "North America" in regions
        assert "Europe" in regions
        
        # Check shipping zones
        zones = data["shipping_zones"]
        assert "Zone_1" in zones
        assert "Zone_2" in zones
        assert "Zone_3" in zones
    
    @patch('src.main.verify_token')
    def test_quotation_invalid_parameters(self, mock_verify_token, client, mock_user):
        """Test quotation endpoints with invalid parameters"""
        mock_verify_token.return_value = mock_user
        
        # Test missing required parameters
        response = client.post(
            "/api/v1/quotations/multi-carrier",
            params={
                "origin_country": "MX",
                # Missing destination_country and other required params
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.main.verify_token')
    def test_quotation_negative_values(self, mock_verify_token, client, mock_user):
        """Test quotation endpoints with negative values"""
        mock_verify_token.return_value = mock_user
        
        response = client.post(
            "/api/v1/quotations/multi-carrier",
            params={
                "origin_country": "MX",
                "destination_country": "US",
                "weight_kg": -1.0,  # Invalid negative weight
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15,
                "value": 150.0
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_quotation_endpoints_unauthorized(self, client):
        """Test quotation endpoints without authentication"""
        endpoints = [
            ("POST", "/api/v1/quotations/multi-carrier", {
                "origin_country": "MX",
                "destination_country": "US",
                "weight_kg": 2.5,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15,
                "value": 150.0
            }),
            ("POST", "/api/v1/quotations/comparison", {
                "origin_country": "MX",
                "destination_country": "US",
                "weight_kg": 2.5,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15,
                "value": 150.0
            }),
            ("GET", "/api/v1/quotations/carriers", None),
            ("GET", "/api/v1/quotations/countries", None),
        ]
        
        for method, url, params in endpoints:
            if method == "POST":
                response = client.post(url, params=params)
            else:
                response = client.get(url)
            
            assert response.status_code == 403  # Forbidden without auth


class TestQuotationErrorHandling:
    """Test cases for error handling in quotation system"""
    
    @pytest.mark.asyncio
    async def test_carrier_integration_error(self, quotation_service):
        """Test handling of carrier integration errors"""
        # Mock factory that returns None (unsupported carrier)
        class ErrorMockFactory:
            @staticmethod
            def create_integration(carrier_code, config, sandbox=True):
                return None  # Simulates unsupported carrier
        
        quotation_service.set_carrier_factory(ErrorMockFactory())
        
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        response = await quotation_service.get_quotations(request)
        
        # Should handle errors gracefully
        assert len(response.errors) > 0
        assert response.successful_carriers == 0
    
    @pytest.mark.asyncio
    async def test_partial_carrier_failure(self, quotation_service):
        """Test handling when some carriers fail"""
        # Mock factory where only some carriers work
        class PartialMockFactory:
            @staticmethod
            def create_integration(carrier_code, config, sandbox=True):
                if carrier_code == "DHL":
                    class WorkingIntegration:
                        async def calculate_rates(self, *args, **kwargs):
                            from src.integrations.base import ShippingRate
                            return [
                                ShippingRate(
                                    carrier="DHL Express",
                                    service_type="Express Worldwide",
                                    base_rate=42.0,
                                    weight_rate=16.25,
                                    fuel_surcharge=6.99,
                                    insurance_rate=0.75,
                                    total_cost=65.99,
                                    currency="USD",
                                    transit_days=3,
                                    valid_until=datetime.utcnow() + timedelta(hours=24)
                                )
                            ]
                    return WorkingIntegration()
                else:
                    # Return None for other carriers
                    return None
        
        quotation_service.set_carrier_factory(PartialMockFactory())
        
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=2.5,
            length_cm=30,
            width_cm=20,
            height_cm=15,
            value=150.0
        )
        
        response = await quotation_service.get_quotations(request)
        
        # Should have one successful quote and some errors
        assert len(response.quotes) > 0
        assert response.successful_carriers == 1
        assert len(response.errors) > 0


# Performance test markers
@pytest.mark.performance
class TestQuotationPerformance:
    """Performance tests for quotation system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_quotation_requests(self, quotation_service):
        """Test concurrent quotation requests performance"""
        requests = [
            QuotationRequest(
                origin_country="MX",
                destination_country="US",
                weight_kg=float(i + 1),
                length_cm=30,
                width_cm=20,
                height_cm=15,
                value=100.0 + i * 10
            )
            for i in range(5)
        ]
        
        start_time = datetime.utcnow()
        
        # Execute multiple quotation requests concurrently
        tasks = [quotation_service.get_quotations(req) for req in requests]
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert processing_time < 5.0  # Less than 5 seconds for 5 concurrent requests
        
        # All should return valid responses
        assert len(results) == 5
        assert all(isinstance(result, QuotationResponse) for result in results)
    
    @pytest.mark.asyncio
    async def test_quotation_response_time(self, quotation_service, sample_quotation_request):
        """Test single quotation response time"""
        start_time = datetime.utcnow()
        
        response = await quotation_service.get_quotations(sample_quotation_request)
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Should complete quickly for single request
        assert processing_time < 2.0  # Less than 2 seconds
        assert response.processing_time_ms < 2000  # Internal timing should also be reasonable
    
    @pytest.mark.asyncio
    async def test_large_value_quotation(self, quotation_service):
        """Test quotation with large value package"""
        request = QuotationRequest(
            origin_country="MX",
            destination_country="US",
            weight_kg=50.0,  # Large package
            length_cm=100,
            width_cm=80,
            height_cm=60,
            value=10000.0  # High value
        )
        
        response = await quotation_service.get_quotations(request)
        
        # Should handle large values correctly
        assert len(response.quotes) > 0
        
        # Insurance rates should scale with value
        for quote in response.quotes:
            if quote.available:
                assert quote.insurance_rate > 0
                assert quote.total_cost > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])