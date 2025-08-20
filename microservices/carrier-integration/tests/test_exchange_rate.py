import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.exchange_rate.banco_republica import BancoRepublicaClient
from src.services.exchange_rate_service import ExchangeRateService


class TestBancoRepublicaClient:
    @pytest.fixture
    def banco_client(self):
        return BancoRepublicaClient()
    
    @pytest.mark.asyncio
    async def test_get_current_trm(self, banco_client):
        """Test getting current TRM from Banco de la República"""
        mock_response = Mock()
        mock_response.value = 4250.50
        mock_response.validityFrom = datetime.now()
        mock_response.validityTo = datetime.now() + timedelta(days=1)
        mock_response.unit = "COP/USD"
        
        with patch.object(banco_client, 'wsdl_url', 'mock_wsdl'):
            with patch('src.exchange_rate.banco_republica.SOAPClient') as mock_soap:
                mock_client = Mock()
                mock_client.service.queryTCRM.return_value = mock_response
                mock_soap.return_value = mock_client
                
                # Clear cache to force API call
                banco_client.cache.clear()
                
                trm_data = await banco_client.get_current_trm()
                
                assert trm_data['rate'] == 4250.50
                assert trm_data['source'] == 'banco_republica'
                assert trm_data['unit'] == 'COP/USD'
    
    @pytest.mark.asyncio
    async def test_trm_cache(self, banco_client):
        """Test TRM caching mechanism"""
        mock_response = Mock()
        mock_response.value = 4250.50
        mock_response.validityFrom = datetime.now()
        mock_response.validityTo = datetime.now() + timedelta(days=1)
        
        with patch.object(banco_client, 'wsdl_url', 'mock_wsdl'):
            with patch('src.exchange_rate.banco_republica.SOAPClient') as mock_soap:
                mock_client = Mock()
                mock_client.service.queryTCRM.return_value = mock_response
                mock_soap.return_value = mock_client
                
                # First call - should hit API
                banco_client.cache.clear()
                trm1 = await banco_client.get_current_trm()
                
                # Second call - should use cache
                trm2 = await banco_client.get_current_trm()
                
                # Verify API was called only once
                mock_client.service.queryTCRM.assert_called_once()
                assert trm1 == trm2
    
    @pytest.mark.asyncio
    async def test_trm_fallback(self, banco_client):
        """Test fallback when Banco de la República service is down"""
        with patch.object(banco_client, 'wsdl_url', 'mock_wsdl'):
            with patch('src.exchange_rate.banco_republica.SOAPClient') as mock_soap:
                mock_soap.side_effect = Exception("Service unavailable")
                
                # Clear cache and last TRM
                banco_client.cache.clear()
                banco_client.last_trm = None
                
                trm_data = await banco_client.get_current_trm()
                
                # Should return fallback value
                assert trm_data['rate'] == 4000.0
                assert trm_data['source'] == 'fallback'
    
    @pytest.mark.asyncio
    async def test_check_trm_variation(self, banco_client):
        """Test TRM variation detection"""
        # Mock today's TRM
        today_response = Mock()
        today_response.value = 4400.00
        today_response.validityFrom = datetime.now()
        today_response.validityTo = datetime.now() + timedelta(days=1)
        
        # Mock yesterday's TRM
        yesterday_response = Mock()
        yesterday_response.value = 4200.00
        yesterday_response.validityFrom = datetime.now() - timedelta(days=1)
        yesterday_response.validityTo = datetime.now()
        
        with patch.object(banco_client, 'wsdl_url', 'mock_wsdl'):
            with patch('src.exchange_rate.banco_republica.SOAPClient') as mock_soap:
                mock_client = Mock()
                mock_client.service.queryTCRM.side_effect = [
                    today_response,
                    yesterday_response
                ]
                mock_soap.return_value = mock_client
                
                # Clear cache
                banco_client.cache.clear()
                
                variation = await banco_client.check_trm_variation(threshold_percentage=3.0)
                
                assert variation is not None
                assert variation['alert'] is True
                assert variation['variation_percentage'] > 3.0
                assert variation['today_rate'] == 4400.00
                assert variation['yesterday_rate'] == 4200.00


class TestExchangeRateService:
    @pytest.fixture
    def exchange_service(self):
        return ExchangeRateService()
    
    @pytest.mark.asyncio
    async def test_currency_conversion_cop_to_usd(self, exchange_service):
        """Test converting COP to USD"""
        # Mock TRM
        exchange_service.current_trm = {
            'rate': 4000.0,
            'source': 'test',
            'valid_date': datetime.now()
        }
        exchange_service.spread = 0.03  # 3% spread
        
        amount_cop = 4000000  # 4 million COP
        amount_usd = await exchange_service.convert(amount_cop, "COP", "USD")
        
        # With 3% spread: 4000 * 1.03 = 4120
        # 4000000 / 4120 ≈ 970.87
        expected_usd = amount_cop / (4000.0 * 1.03)
        assert abs(amount_usd - expected_usd) < 0.01
    
    @pytest.mark.asyncio
    async def test_currency_conversion_usd_to_cop(self, exchange_service):
        """Test converting USD to COP"""
        # Mock TRM
        exchange_service.current_trm = {
            'rate': 4000.0,
            'source': 'test',
            'valid_date': datetime.now()
        }
        exchange_service.spread = 0.03  # 3% spread
        
        amount_usd = 1000  # 1000 USD
        amount_cop = await exchange_service.convert(amount_usd, "USD", "COP")
        
        # With 3% spread: 4000 * 1.03 = 4120
        # 1000 * 4120 = 4,120,000
        expected_cop = amount_usd * (4000.0 * 1.03)
        assert abs(amount_cop - expected_cop) < 0.01
    
    @pytest.mark.asyncio
    async def test_same_currency_conversion(self, exchange_service):
        """Test converting same currency returns same amount"""
        amount = 1000.0
        result = await exchange_service.convert(amount, "USD", "USD")
        assert result == amount
    
    @pytest.mark.asyncio
    async def test_get_current_trm_with_spread(self, exchange_service):
        """Test getting current TRM with spread applied"""
        # Mock TRM
        exchange_service.current_trm = {
            'rate': 4000.0,
            'source': 'banco_republica',
            'valid_date': datetime.now(),
            'valid_until': datetime.now() + timedelta(days=1)
        }
        exchange_service.spread = 0.025  # 2.5% spread
        
        trm_data = await exchange_service.get_current_trm()
        
        assert trm_data['rate'] == 4000.0
        assert trm_data['spread'] == 0.025
        assert trm_data['effective_rate'] == 4000.0 * 1.025
        assert trm_data['from_currency'] == 'COP'
        assert trm_data['to_currency'] == 'USD'
    
    @pytest.mark.asyncio
    async def test_unsupported_currency_pair(self, exchange_service):
        """Test error handling for unsupported currency pairs"""
        with pytest.raises(ValueError, match="Unsupported currency pair"):
            await exchange_service.get_rate("EUR", "GBP")


@pytest.mark.asyncio
async def test_scheduled_trm_update():
    """Test scheduled TRM update functionality"""
    from src.services.exchange_rate_service import ExchangeRateService
    from unittest.mock import MagicMock
    
    service = ExchangeRateService()
    
    # Mock the update_trm method
    service.update_trm = AsyncMock()
    
    # Start scheduler (but don't wait for scheduled time)
    await service.start_scheduler()
    
    # Manually trigger update
    await service.update_trm()
    
    # Verify update was called
    service.update_trm.assert_called()
    
    # Stop scheduler
    await service.stop_scheduler()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])