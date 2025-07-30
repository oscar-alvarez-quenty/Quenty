"""
Unit tests for SCRUM-14: Exchange Rate API Integration
Tests cover Banco de la República integration, TRM fetching, currency conversion, and automated updates
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date, timedelta
import json
import httpx

from src.main import app
from src.exchange_rate.banrep import BanrepAPIClient, ExchangeRateService, ExchangeRate
from src.exchange_rate.scheduler import ExchangeRateScheduler, ExchangeRateModel


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
        "permissions": ["admin:exchange_rates"],
        "is_superuser": False
    }


@pytest.fixture
def sample_exchange_rate():
    """Sample exchange rate for testing"""
    return ExchangeRate(
        currency_from="USD",
        currency_to="COP",
        rate=4250.75,
        date=date.today(),
        source="Banco de la República",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def banrep_client():
    """BanrepAPIClient fixture"""
    return BanrepAPIClient()


@pytest.fixture
def exchange_service():
    """ExchangeRateService fixture"""
    return ExchangeRateService()


class TestBanrepAPIClient:
    """Test cases for Banco de la República API client"""
    
    def test_client_initialization(self, banrep_client):
        """Test client initialization"""
        assert banrep_client.base_url == "https://www.banrep.gov.co/TasaCambio/TRM.jsp"
        assert banrep_client.api_url == "https://www.banrep.gov.co/TasaCambio/TRMQueryEngine.jsp"
        assert banrep_client.timeout == 30.0
    
    @pytest.mark.asyncio
    async def test_get_trm_success(self, banrep_client):
        """Test successful TRM fetching"""
        target_date = date(2025, 7, 30)
        
        # Mock successful API response
        mock_response = {
            "valor": 4250.75,
            "fecha": "2025-07-30",
            "unidad": "COP"
        }
        
        # Mock httpx response
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [mock_response]
            mock_get.return_value = mock_resp
            
            rate = await banrep_client.get_trm_for_date(target_date)
            
            assert rate is not None
            assert rate.currency_from == "USD"
            assert rate.currency_to == "COP"
            assert rate.rate == 4250.75
            assert rate.date == target_date
            assert rate.source == "Banco de la República"
    
    @pytest.mark.asyncio
    async def test_get_trm_api_error(self, banrep_client):
        """Test TRM fetching with API error"""
        target_date = date(2025, 7, 30)
        
        # Mock API error response
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 500
            mock_get.return_value = mock_resp
            
            # Should fallback to alternative method
            with patch.object(banrep_client, '_get_fallback_trm', return_value=None) as mock_fallback:
                rate = await banrep_client.get_trm_for_date(target_date)
                
                assert rate is None
                mock_fallback.assert_called_once_with(target_date)
    
    @pytest.mark.asyncio
    async def test_get_trm_timeout(self, banrep_client):
        """Test TRM fetching with timeout"""
        target_date = date(2025, 7, 30)
        
        # Mock timeout exception
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            with patch.object(banrep_client, '_get_fallback_trm', return_value=None) as mock_fallback:
                rate = await banrep_client.get_trm_for_date(target_date)
                
                assert rate is None
                mock_fallback.assert_called_once_with(target_date)
    
    @pytest.mark.asyncio
    async def test_get_trm_invalid_data(self, banrep_client):
        """Test TRM fetching with invalid data"""
        target_date = date(2025, 7, 30)
        
        # Mock response with invalid data
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = []  # Empty response
            mock_get.return_value = mock_resp
            
            with patch.object(banrep_client, '_get_fallback_trm', return_value=None) as mock_fallback:
                rate = await banrep_client.get_trm_for_date(target_date)
                
                assert rate is None
                mock_fallback.assert_called_once_with(target_date)
    
    @pytest.mark.asyncio
    async def test_fallback_trm_xml_success(self, banrep_client):
        """Test fallback TRM method with XML response"""
        target_date = date(2025, 7, 30)
        xml_content = """<?xml version="1.0"?>
        <trm>
            <valor>4,250.75</valor>
            <fecha>30/07/2025</fecha>
        </trm>"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.text = xml_content
            mock_get.return_value = mock_resp
            
            rate = await banrep_client._get_fallback_trm(target_date)
            
            assert rate is not None
            assert rate.rate == 4250.75
            assert rate.source == "Banco de la República (fallback)"
    
    @pytest.mark.asyncio
    async def test_get_current_trm(self, banrep_client):
        """Test getting current TRM"""
        with patch.object(banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_rate = ExchangeRate(
                currency_from="USD",
                currency_to="COP",
                rate=4250.75,
                date=date.today(),
                source="Banco de la República",
                created_at=datetime.utcnow()
            )
            mock_get_trm.return_value = mock_rate
            
            rate = await banrep_client.get_current_trm()
            
            assert rate is not None
            assert rate.rate == 4250.75
            mock_get_trm.assert_called_once_with(date.today())
    
    @pytest.mark.asyncio
    async def test_get_trm_history(self, banrep_client):
        """Test getting TRM history"""
        start_date = date(2025, 7, 28)  # Monday
        end_date = date(2025, 7, 30)    # Wednesday
        
        with patch.object(banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_rates = [
                ExchangeRate(
                    currency_from="USD",
                    currency_to="COP",
                    rate=4250.75,
                    date=date(2025, 7, 28),
                    source="Banco de la República",
                    created_at=datetime.utcnow()
                ),
                ExchangeRate(
                    currency_from="USD",
                    currency_to="COP",
                    rate=4251.25,
                    date=date(2025, 7, 29),
                    source="Banco de la República",
                    created_at=datetime.utcnow()
                ),
                ExchangeRate(
                    currency_from="USD",
                    currency_to="COP",
                    rate=4252.00,
                    date=date(2025, 7, 30),
                    source="Banco de la República",
                    created_at=datetime.utcnow()
                )
            ]
            mock_get_trm.side_effect = mock_rates
            
            # Mock asyncio.sleep to speed up test
            with patch('asyncio.sleep'):
                rates = await banrep_client.get_trm_history(start_date, end_date)
            
            assert len(rates) == 3
            assert all(isinstance(rate, ExchangeRate) for rate in rates)
            assert rates[0].rate == 4250.75
            assert rates[2].rate == 4252.00
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, banrep_client):
        """Test connection validation success"""
        with patch.object(banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_get_trm.return_value = ExchangeRate(
                currency_from="USD",
                currency_to="COP",
                rate=4250.75,
                date=date.today() - timedelta(days=1),
                source="Banco de la República",
                created_at=datetime.utcnow()
            )
            
            is_valid = await banrep_client.validate_connection()
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, banrep_client):
        """Test connection validation failure"""
        with patch.object(banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_get_trm.return_value = None
            
            is_valid = await banrep_client.validate_connection()
            
            assert is_valid is False


class TestExchangeRateService:
    """Test cases for ExchangeRateService"""
    
    @pytest.mark.asyncio
    async def test_get_usd_cop_rate(self, exchange_service, sample_exchange_rate):
        """Test getting USD to COP exchange rate"""
        with patch.object(exchange_service.banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_get_trm.return_value = sample_exchange_rate
            
            rate = await exchange_service.get_exchange_rate("USD", "COP")
            
            assert rate is not None
            assert rate.currency_from == "USD"
            assert rate.currency_to == "COP"
            assert rate.rate == 4250.75
    
    @pytest.mark.asyncio
    async def test_get_cop_usd_rate(self, exchange_service, sample_exchange_rate):
        """Test getting COP to USD exchange rate (inverse)"""
        with patch.object(exchange_service.banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_get_trm.return_value = sample_exchange_rate
            
            rate = await exchange_service.get_exchange_rate("COP", "USD")
            
            assert rate is not None
            assert rate.currency_from == "COP"
            assert rate.currency_to == "USD"
            assert rate.rate == pytest.approx(1.0 / 4250.75, rel=1e-6)
            assert rate.source.endswith("(inverse)")
    
    @pytest.mark.asyncio
    async def test_get_unsupported_currency_pair(self, exchange_service):
        """Test getting unsupported currency pair"""
        rate = await exchange_service.get_exchange_rate("EUR", "GBP")
        
        assert rate is None
    
    @pytest.mark.asyncio
    async def test_convert_amount_usd_to_cop(self, exchange_service, sample_exchange_rate):
        """Test currency conversion USD to COP"""
        with patch.object(exchange_service, 'get_exchange_rate') as mock_get_rate:
            mock_get_rate.return_value = sample_exchange_rate
            
            converted = await exchange_service.convert_amount(100.0, "USD", "COP")
            
            assert converted == pytest.approx(425075.0, rel=1e-6)
    
    @pytest.mark.asyncio
    async def test_convert_same_currency(self, exchange_service):
        """Test conversion with same currency"""
        converted = await exchange_service.convert_amount(100.0, "USD", "USD")
        
        assert converted == 100.0
    
    @pytest.mark.asyncio
    async def test_convert_amount_unavailable_rate(self, exchange_service):
        """Test conversion with unavailable exchange rate"""
        with patch.object(exchange_service, 'get_exchange_rate') as mock_get_rate:
            mock_get_rate.return_value = None
            
            converted = await exchange_service.convert_amount(100.0, "EUR", "GBP")
            
            assert converted is None
    
    @pytest.mark.asyncio
    async def test_get_current_usd_cop_rate(self, exchange_service, sample_exchange_rate):
        """Test getting current USD to COP rate"""
        with patch.object(exchange_service.banrep_client, 'get_current_trm') as mock_get_trm:
            mock_get_trm.return_value = sample_exchange_rate
            
            rate = await exchange_service.get_current_usd_cop_rate()
            
            assert rate == 4250.75
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, exchange_service):
        """Test health check when service is healthy"""
        with patch.object(exchange_service.banrep_client, 'validate_connection') as mock_validate:
            with patch.object(exchange_service, 'get_current_usd_cop_rate') as mock_get_rate:
                mock_validate.return_value = True
                mock_get_rate.return_value = 4250.75
                
                health = await exchange_service.health_check()
                
                assert health["service"] == "exchange_rate"
                assert health["status"] == "healthy"
                assert health["banrep_connection"] is True
                assert health["current_usd_cop_rate"] == 4250.75
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, exchange_service):
        """Test health check when service is degraded"""
        with patch.object(exchange_service.banrep_client, 'validate_connection') as mock_validate:
            mock_validate.return_value = False
            
            health = await exchange_service.health_check()
            
            assert health["service"] == "exchange_rate"
            assert health["status"] == "degraded"
            assert health["banrep_connection"] is False
    
    def test_cache_functionality(self, exchange_service):
        """Test exchange rate caching"""
        # Test that cache is initially empty
        assert len(exchange_service._cache) == 0
        
        # Simulate adding to cache
        cache_key = "USD_COP_2025-07-30"
        test_rate = ExchangeRate(
            currency_from="USD",
            currency_to="COP",
            rate=4250.75,
            date=date(2025, 7, 30),
            source="Test",
            created_at=datetime.utcnow()
        )
        
        exchange_service._cache[cache_key] = (test_rate, datetime.utcnow())
        
        assert len(exchange_service._cache) == 1
        assert exchange_service._cache[cache_key][0].rate == 4250.75


class TestExchangeRateScheduler:
    """Test cases for ExchangeRateScheduler"""
    
    @pytest.fixture
    def scheduler(self, exchange_service):
        """ExchangeRateScheduler fixture"""
        return ExchangeRateScheduler(exchange_service)
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """Test scheduler start and stop"""
        assert scheduler._running is False
        
        # Mock the scheduler loop to prevent actual scheduling
        with patch.object(scheduler, '_scheduler_loop') as mock_loop:
            await scheduler.start()
            
            assert scheduler._running is True
            mock_loop.assert_called_once()
            
            await scheduler.stop()
            
            assert scheduler._running is False
    
    @pytest.mark.asyncio
    async def test_manual_update_success(self, scheduler, sample_exchange_rate):
        """Test manual exchange rate update success"""
        target_date = date(2025, 7, 30)
        
        with patch.object(scheduler.exchange_service.banrep_client, 'get_trm_for_date') as mock_get_trm:
            with patch.object(scheduler, '_store_exchange_rate') as mock_store:
                mock_get_trm.return_value = sample_exchange_rate
                mock_store.return_value = True
                
                result = await scheduler.manual_update(target_date)
                
                assert result["success"] is True
                assert result["date"] == target_date.isoformat()
                assert result["rate"] == 4250.75
                assert result["source"] == "Banco de la República"
    
    @pytest.mark.asyncio
    async def test_manual_update_failure(self, scheduler):
        """Test manual exchange rate update failure"""
        target_date = date(2025, 7, 30)
        
        with patch.object(scheduler.exchange_service.banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_get_trm.return_value = None
            
            result = await scheduler.manual_update(target_date)
            
            assert result["success"] is False
            assert "Failed to fetch TRM" in result["message"]
    
    @pytest.mark.asyncio
    async def test_perform_daily_update(self, scheduler, sample_exchange_rate):
        """Test daily update performance"""
        with patch.object(scheduler.exchange_service.banrep_client, 'get_current_trm') as mock_get_trm:
            with patch.object(scheduler, '_store_exchange_rate') as mock_store:
                with patch.object(scheduler, '_fetch_missing_rates') as mock_fetch_missing:
                    mock_get_trm.return_value = sample_exchange_rate
                    mock_store.return_value = True
                    
                    await scheduler._perform_daily_update()
                    
                    mock_get_trm.assert_called_once()
                    mock_store.assert_called_once_with(sample_exchange_rate)
                    mock_fetch_missing.assert_called_once()


class TestExchangeRateEndpoints:
    """Test cases for exchange rate API endpoints"""
    
    @patch('src.main.verify_token')
    def test_get_current_exchange_rate(self, mock_verify_token, client, mock_user, sample_exchange_rate):
        """Test getting current exchange rate endpoint"""
        mock_verify_token.return_value = mock_user
        
        with patch('src.main.exchange_rate_service.get_exchange_rate') as mock_get_rate:
            mock_get_rate.return_value = sample_exchange_rate
            
            response = client.get("/api/v1/exchange-rates/current?from_currency=USD&to_currency=COP")
            
            assert response.status_code == 200
            data = response.json()
            assert data["from_currency"] == "USD"
            assert data["to_currency"] == "COP"
            assert data["rate"] == 4250.75
            assert data["source"] == "Banco de la República"
    
    @patch('src.main.verify_token')
    def test_get_current_exchange_rate_not_found(self, mock_verify_token, client, mock_user):
        """Test getting current exchange rate when not available"""
        mock_verify_token.return_value = mock_user
        
        with patch('src.main.exchange_rate_service.get_exchange_rate') as mock_get_rate:
            mock_get_rate.return_value = None
            
            response = client.get("/api/v1/exchange-rates/current?from_currency=EUR&to_currency=GBP")
            
            assert response.status_code == 404
            assert "not available" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_convert_currency(self, mock_verify_token, client, mock_user, sample_exchange_rate):
        """Test currency conversion endpoint"""
        mock_verify_token.return_value = mock_user
        
        with patch('src.main.exchange_rate_service.convert_amount') as mock_convert:
            with patch('src.main.exchange_rate_service.get_exchange_rate') as mock_get_rate:
                mock_convert.return_value = 425075.0
                mock_get_rate.return_value = sample_exchange_rate
                
                response = client.post("/api/v1/exchange-rates/convert?amount=100&from_currency=USD&to_currency=COP")
                
                assert response.status_code == 200
                data = response.json()
                assert data["original_amount"] == 100.0
                assert data["converted_amount"] == 425075.0
                assert data["from_currency"] == "USD"
                assert data["to_currency"] == "COP"
                assert data["exchange_rate"] == 4250.75
    
    @patch('src.main.verify_token')
    def test_convert_currency_invalid_amount(self, mock_verify_token, client, mock_user):
        """Test currency conversion with invalid amount"""
        mock_verify_token.return_value = mock_user
        
        response = client.post("/api/v1/exchange-rates/convert?amount=-100&from_currency=USD&to_currency=COP")
        
        assert response.status_code == 400
        assert "must be positive" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_get_current_trm(self, mock_verify_token, client, mock_user):
        """Test getting current TRM endpoint"""
        mock_verify_token.return_value = mock_user
        
        with patch('src.main.exchange_rate_service.get_current_usd_cop_rate') as mock_get_trm:
            mock_get_trm.return_value = 4250.75
            
            response = client.get("/api/v1/exchange-rates/trm")
            
            assert response.status_code == 200
            data = response.json()
            assert data["trm"] == 4250.75
            assert data["currency_pair"] == "USD/COP"
            assert data["source"] == "Banco de la República"
            assert data["description"] == "Tasa Representativa del Mercado"
    
    @patch('src.main.verify_token')
    def test_get_current_trm_not_available(self, mock_verify_token, client, mock_user):
        """Test getting current TRM when not available"""
        mock_verify_token.return_value = mock_user
        
        with patch('src.main.exchange_rate_service.get_current_usd_cop_rate') as mock_get_trm:
            mock_get_trm.return_value = None
            
            response = client.get("/api/v1/exchange-rates/trm")
            
            assert response.status_code == 404
            assert "not available" in response.json()["detail"]
    
    @patch('src.main.verify_token')
    def test_manual_exchange_rate_update(self, mock_verify_token, client, mock_user):
        """Test manual exchange rate update endpoint"""
        mock_user["permissions"].append("admin:exchange_rates")
        mock_verify_token.return_value = mock_user
        
        with patch('src.main.get_scheduler') as mock_get_scheduler:
            mock_scheduler = Mock()
            mock_scheduler.manual_update.return_value = {
                "success": True,
                "date": "2025-07-30",
                "rate": 4250.75,
                "source": "Banco de la República",
                "message": "TRM updated: 4250.75 COP/USD"
            }
            mock_get_scheduler.return_value = mock_scheduler
            
            response = client.post("/api/v1/exchange-rates/update")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["rate"] == 4250.75
    
    @patch('src.main.verify_token')
    def test_exchange_rate_health_check(self, mock_verify_token, client, mock_user):
        """Test exchange rate health check endpoint"""
        mock_verify_token.return_value = mock_user
        
        mock_health = {
            "service": "exchange_rate",
            "status": "healthy",
            "banrep_connection": True,
            "current_usd_cop_rate": 4250.75
        }
        
        with patch('src.main.exchange_rate_service.health_check') as mock_health_check:
            mock_health_check.return_value = mock_health
            
            response = client.get("/api/v1/exchange-rates/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "exchange_rate"
            assert data["status"] == "healthy"
            assert data["banrep_connection"] is True
    
    def test_exchange_rate_endpoints_unauthorized(self, client):
        """Test exchange rate endpoints without authentication"""
        endpoints = [
            ("GET", "/api/v1/exchange-rates/current", None),
            ("POST", "/api/v1/exchange-rates/convert?amount=100&from_currency=USD&to_currency=COP", None),
            ("GET", "/api/v1/exchange-rates/trm", None),
            ("GET", "/api/v1/exchange-rates/health", None),
        ]
        
        for method, url, json_data in endpoints:
            if method == "POST":
                response = client.post(url, json=json_data)
            else:
                response = client.get(url)
            
            assert response.status_code == 403  # Forbidden without auth


class TestExchangeRateErrorHandling:
    """Test cases for error handling in exchange rate integration"""
    
    @pytest.mark.asyncio
    async def test_api_network_error(self, banrep_client):
        """Test handling of network errors"""
        target_date = date(2025, 7, 30)
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.NetworkError("Network unreachable")
            
            with patch.object(banrep_client, '_get_fallback_trm', return_value=None):
                rate = await banrep_client.get_trm_for_date(target_date)
                
                assert rate is None
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, banrep_client):
        """Test handling of invalid JSON response"""
        target_date = date(2025, 7, 30)
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_resp
            
            with patch.object(banrep_client, '_get_fallback_trm', return_value=None):
                rate = await banrep_client.get_trm_for_date(target_date)
                
                assert rate is None
    
    @pytest.mark.asyncio
    async def test_scheduler_error_handling(self, exchange_service):
        """Test scheduler error handling"""
        scheduler = ExchangeRateScheduler(exchange_service)
        
        with patch.object(scheduler.exchange_service.banrep_client, 'get_current_trm') as mock_get_trm:
            mock_get_trm.side_effect = Exception("API Error")
            
            # Should not raise exception, should handle gracefully
            await scheduler._perform_daily_update()
            
            # Verify error was logged (would need logging setup to test properly)
            mock_get_trm.assert_called_once()


# Performance test markers
@pytest.mark.performance
class TestExchangeRatePerformance:
    """Performance tests for exchange rate integration"""
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_requests(self, exchange_service):
        """Test concurrent exchange rate requests"""
        target_dates = [
            date(2025, 7, 28),
            date(2025, 7, 29),
            date(2025, 7, 30)
        ]
        
        with patch.object(exchange_service.banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_rates = [
                ExchangeRate(
                    currency_from="USD",
                    currency_to="COP",
                    rate=4250.0 + i,
                    date=target_dates[i],
                    source="Banco de la República",
                    created_at=datetime.utcnow()
                ) for i in range(3)
            ]
            mock_get_trm.side_effect = mock_rates
            
            # Execute concurrent requests
            start_time = datetime.utcnow()
            tasks = [
                exchange_service.get_exchange_rate("USD", "COP", target_date)
                for target_date in target_dates
            ]
            results = await asyncio.gather(*tasks)
            end_time = datetime.utcnow()
            
            # Should complete quickly with concurrent execution
            processing_time = (end_time - start_time).total_seconds()
            assert processing_time < 2.0  # Less than 2 seconds
            
            # All should return results
            assert len(results) == 3
            assert all(rate is not None for rate in results)
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, exchange_service):
        """Test cache performance improvement"""
        target_date = date(2025, 7, 30)
        
        with patch.object(exchange_service.banrep_client, 'get_trm_for_date') as mock_get_trm:
            mock_rate = ExchangeRate(
                currency_from="USD",
                currency_to="COP",
                rate=4250.75,
                date=target_date,
                source="Banco de la República",
                created_at=datetime.utcnow()
            )
            mock_get_trm.return_value = mock_rate
            
            # First call should hit the API
            start_time = datetime.utcnow()
            rate1 = await exchange_service.get_exchange_rate("USD", "COP", target_date)
            first_call_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Second call should use cache
            start_time = datetime.utcnow()
            rate2 = await exchange_service.get_exchange_rate("USD", "COP", target_date)
            second_call_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Cache should be faster
            assert second_call_time < first_call_time
            assert rate1.rate == rate2.rate
            assert mock_get_trm.call_count == 1  # Only called once due to cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])