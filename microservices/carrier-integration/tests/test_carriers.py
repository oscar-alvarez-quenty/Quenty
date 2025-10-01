import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import httpx

from src.carriers.dhl import DHLClient
from src.carriers.fedex import FedExClient
from src.carriers.ups import UPSClient
from src.carriers.servientrega import ServientregaClient
from src.carriers.interrapidisimo import InterrapidisimoClient
from src.schemas import (
    QuoteRequest, QuoteResponse,
    LabelRequest, LabelResponse,
    TrackingResponse, TrackingEvent,
    PickupRequest, PickupResponse,
    Address, Package
)


class TestDHLClient:
    @pytest.fixture
    def dhl_client(self):
        credentials = {
            'username': 'test_user',
            'password': 'test_pass',
            'account_number': 'TEST123',
            'message_reference': 'TEST_REF'
        }
        return DHLClient(credentials, 'sandbox')
    
    @pytest.fixture
    def sample_quote_request(self):
        return QuoteRequest(
            origin=Address(
                street="123 Test St",
                city="Bogota",
                state="DC",
                postal_code="110111",
                country="CO",
                contact_name="Test Sender",
                contact_phone="+573001234567"
            ),
            destination=Address(
                street="456 Main St",
                city="New York",
                state="NY",
                postal_code="10001",
                country="US",
                contact_name="Test Receiver",
                contact_phone="+12125551234"
            ),
            packages=[
                Package(
                    weight_kg=5.0,
                    length_cm=30,
                    width_cm=20,
                    height_cm=15,
                    declared_value=100,
                    currency="USD"
                )
            ],
            service_type="express"
        )
    
    @pytest.mark.asyncio
    async def test_get_quote_success(self, dhl_client, sample_quote_request):
        mock_response = {
            'products': [{
                'productName': 'DHL Express Worldwide',
                'totalPrice': [{'price': 150.00, 'currency': 'USD'}],
                'deliveryCapabilities': {'totalTransitDays': '3'},
                'totalPriceBreakdown': [{
                    'priceBreakdown': [{'price': 10.00}]
                }]
            }]
        }
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            quote = await dhl_client.get_quote(sample_quote_request)
            
            assert isinstance(quote, QuoteResponse)
            assert quote.carrier == "DHL"
            assert quote.amount == 150.00
            assert quote.currency == "USD"
            assert quote.estimated_days == 3
    
    @pytest.mark.asyncio
    async def test_generate_label_success(self, dhl_client):
        label_request = LabelRequest(
            carrier="DHL",
            order_id="TEST-ORDER-001",
            origin=Address(
                street="123 Test St",
                city="Bogota",
                postal_code="110111",
                country="CO",
                contact_name="Test Sender",
                contact_phone="+573001234567"
            ),
            destination=Address(
                street="456 Main St",
                city="New York",
                postal_code="10001",
                country="US",
                contact_name="Test Receiver",
                contact_phone="+12125551234"
            ),
            packages=[
                Package(
                    weight_kg=5.0,
                    length_cm=30,
                    width_cm=20,
                    height_cm=15
                )
            ],
            service_type="express"
        )
        
        mock_response = {
            'shipmentTrackingNumber': 'DHL123456789',
            'shipmentIdentificationNumber': 'AWB123456',
            'documents': [{
                'typeCode': 'label',
                'content': 'base64_encoded_label_data'
            }],
            'totalPrice': [{'price': 150.00, 'currency': 'USD'}]
        }
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            label = await dhl_client.generate_label(label_request)
            
            assert isinstance(label, LabelResponse)
            assert label.tracking_number == 'DHL123456789'
            assert label.awb_number == 'AWB123456'
            assert label.label_data == 'base64_encoded_label_data'


class TestFedExClient:
    @pytest.fixture
    def fedex_client(self):
        credentials = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'account_number': 'TEST456'
        }
        return FedExClient(credentials, 'sandbox')
    
    @pytest.mark.asyncio
    async def test_oauth_token_refresh(self, fedex_client):
        mock_token_response = {
            'access_token': 'new_token_123',
            'expires_in': 3600
        }
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_token_response
            mock_post.return_value.raise_for_status = Mock()
            
            token = await fedex_client._get_access_token()
            
            assert token == 'new_token_123'
            assert fedex_client.access_token == 'new_token_123'
            assert fedex_client.token_expires is not None


class TestUPSClient:
    @pytest.fixture
    def ups_client(self):
        credentials = {
            'client_id': 'test_ups_client',
            'client_secret': 'test_ups_secret',
            'shipper_number': 'UPS789',
            'merchant_id': 'TEST_MERCHANT'
        }
        return UPSClient(credentials, 'sandbox')
    
    @pytest.mark.asyncio
    async def test_address_validation(self, ups_client):
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="US",
            contact_name="Test",
            contact_phone="+12125551234"
        )
        
        mock_response = {
            'XAVResponse': {
                'ValidAddressIndicator': 'Y'
            }
        }
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            # Mock token response
            mock_post.return_value.json.side_effect = [
                {'access_token': 'test_token', 'expires_in': 3600},
                mock_response
            ]
            mock_post.return_value.raise_for_status = Mock()
            
            is_valid = await ups_client.validate_address(address)
            
            assert is_valid is True


class TestServientregaClient:
    @pytest.fixture
    def servientrega_client(self):
        credentials = {
            'username': 'test_servientrega',
            'password': 'test_pass',
            'agreement_code': 'CONV123'
        }
        return ServientregaClient(credentials, 'sandbox')
    
    @pytest.mark.asyncio
    async def test_get_city_code(self, servientrega_client):
        with patch.object(servientrega_client.soap_client.service, 'ConsultarCiudad') as mock_consultar:
            mock_response = Mock()
            mock_response.Exitoso = True
            mock_response.CodigoCiudad = '11001'
            mock_consultar.return_value = mock_response
            
            city_code = await servientrega_client._get_city_code('Bogotá', '110111')
            
            assert city_code == '11001'
    
    @pytest.mark.asyncio
    async def test_check_coverage(self, servientrega_client):
        with patch.object(servientrega_client.soap_client.service, 'ConsultarCobertura') as mock_cobertura:
            mock_response = Mock()
            mock_response.TieneCobertura = True
            mock_cobertura.return_value = mock_response
            
            has_coverage = await servientrega_client.check_coverage('Medellín', '050001')
            
            assert has_coverage is True


class TestInterrapidisimoClient:
    @pytest.fixture
    def interrapidisimo_client(self):
        credentials = {
            'api_key': 'test_api_key',
            'client_id': 'test_client_id',
            'customer_code': 'CUST123'
        }
        return InterrapidisimoClient(credentials, 'sandbox')
    
    @pytest.mark.asyncio
    async def test_get_coverage(self, interrapidisimo_client):
        mock_response = {
            'success': True,
            'data': {
                'ciudades': [
                    {'nombre': 'Bogotá', 'codigoPostal': '110111'},
                    {'nombre': 'Medellín', 'codigoPostal': '050001'}
                ]
            }
        }
        
        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = Mock()
            
            coverage = await interrapidisimo_client.get_coverage('Bogotá')
            
            assert len(coverage) == 2
            assert coverage[0]['nombre'] == 'Bogotá'
    
    @pytest.mark.asyncio
    async def test_generate_manifest(self, interrapidisimo_client):
        tracking_numbers = ['INTER001', 'INTER002', 'INTER003']
        
        mock_response = {
            'success': True,
            'data': {
                'numeroManifiesto': 'MAN123456',
                'urlManifiesto': 'https://api.interrapidisimo.co/manifests/MAN123456.pdf',
                'manifestoPDF': 'base64_encoded_pdf'
            }
        }
        
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = Mock()
            
            manifest = await interrapidisimo_client.generate_manifest(tracking_numbers)
            
            assert manifest['manifest_number'] == 'MAN123456'
            assert 'manifest_url' in manifest
            assert 'manifest_pdf' in manifest


@pytest.mark.asyncio
async def test_carrier_fallback():
    """Test fallback between carriers when primary fails"""
    from src.services.fallback_service import FallbackService
    
    fallback_service = FallbackService()
    
    # Configure fallback priority
    await fallback_service.configure_priority(
        route="CO-US",
        carriers=["DHL", "FedEx", "UPS"]
    )
    
    # Test primary carrier selection
    primary = await fallback_service.select_primary_carrier("CO-US")
    assert primary == "DHL"
    
    # Test fallback carrier selection
    fallback = await fallback_service.select_fallback_carrier("CO-US", exclude=["DHL"])
    assert fallback == "FedEx"
    
    # Test second fallback
    second_fallback = await fallback_service.select_fallback_carrier(
        "CO-US", 
        exclude=["DHL", "FedEx"]
    )
    assert second_fallback == "UPS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])