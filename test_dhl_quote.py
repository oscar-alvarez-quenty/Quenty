#!/usr/bin/env python3
"""Test DHL Quote with new authentication"""

import asyncio
import httpx
from datetime import datetime, timedelta
import json

async def test_direct_dhl_api():
    """Test DHL API directly with new authentication"""

    # DHL Credentials (new authentication method)
    USERNAME = "quentysasCO"
    PASSWORD = "M#6bM^7wW!7dV^1n"
    ACCOUNT_NUMBER = "683146118"

    url = "https://express.api.dhl.com/mydhlapi/test/rates"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Test different routes
    test_cases = [
        {
            "name": "Colombia to Peru",
            "shipper": {"postalCode": "760001", "cityName": "Cali", "countryCode": "CO"},
            "receiver": {"postalCode": "LIMA 01", "cityName": "Lima", "countryCode": "PE"}
        },
        {
            "name": "Colombia to USA",
            "shipper": {"postalCode": "110111", "cityName": "Bogota", "countryCode": "CO"},
            "receiver": {"postalCode": "33101", "cityName": "Miami", "countryCode": "US"}
        },
        {
            "name": "Colombia to Mexico",
            "shipper": {"postalCode": "050001", "cityName": "Medellin", "countryCode": "CO"},
            "receiver": {"postalCode": "06600", "cityName": "Mexico City", "countryCode": "MX"}
        }
    ]

    async with httpx.AsyncClient() as client:
        for test in test_cases:
            print(f"\n{'='*60}")
            print(f"Testing: {test['name']}")
            print(f"{'='*60}")

            payload = {
                "customerDetails": {
                    "shipperDetails": test["shipper"],
                    "receiverDetails": test["receiver"]
                },
                "accounts": [
                    {
                        "typeCode": "shipper",
                        "number": ACCOUNT_NUMBER
                    }
                ],
                "plannedShippingDateAndTime": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT14:00:00GMT+00:00"),
                "unitOfMeasurement": "metric",
                "isCustomsDeclarable": True,
                "packages": [
                    {
                        "weight": 5,
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 15
                        }
                    }
                ],
                "monetaryAmount": [
                    {
                        "typeCode": "declaredValue",
                        "value": 100,
                        "currency": "USD"
                    }
                ]
            }

            try:
                response = await client.post(
                    url,
                    headers=headers,
                    auth=(USERNAME, PASSWORD),
                    json=payload,
                    timeout=30.0
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Found {len(data.get('products', []))} shipping options")

                    for product in data.get('products', [])[:3]:
                        print(f"\nService: {product.get('productName')}")
                        if 'totalPrice' in product and product['totalPrice']:
                            price_info = product['totalPrice'][0] if isinstance(product['totalPrice'], list) else product['totalPrice']
                            print(f"Price: {price_info.get('price')} {price_info.get('currency', 'USD')}")

                        if 'deliveryCapabilities' in product:
                            delivery = product['deliveryCapabilities']
                            if 'totalTransitDays' in delivery:
                                print(f"Transit Days: {delivery['totalTransitDays']}")
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:200]}")

            except Exception as e:
                print(f"❌ Exception: {str(e)}")

async def test_carrier_integration_api():
    """Test through carrier integration service"""

    print(f"\n{'='*60}")
    print("Testing via Carrier Integration Service")
    print(f"{'='*60}")

    url = "http://localhost:8009/api/v1/quotes"

    test_payload = {
        "carrier": "DHL",
        "origin": {
            "street": "Calle 100 #15-20",
            "city": "Bogota",
            "state": "Cundinamarca",
            "postal_code": "110111",
            "country": "CO",
            "contact_name": "Juan Perez",
            "contact_phone": "+573001234567",
            "contact_email": "juan@example.com",
            "company": "Quenty SAS"
        },
        "destination": {
            "street": "1234 Ocean Drive",
            "city": "Miami",
            "state": "FL",
            "postal_code": "33139",
            "country": "US",
            "contact_name": "John Doe",
            "contact_phone": "+13051234567",
            "contact_email": "john@example.com"
        },
        "packages": [
            {
                "weight_kg": 10,
                "length_cm": 40,
                "width_cm": 30,
                "height_cm": 25,
                "description": "Electronics",
                "declared_value": 500,
                "currency": "USD"
            }
        ],
        "service_type": "express",
        "insurance_required": True,
        "customs_value": 500
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=test_payload,
                timeout=30.0
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ Quote received successfully!")
                print(f"Quote ID: {data.get('quote_id')}")
                print(f"Carrier: {data.get('carrier')}")
                print(f"Service: {data.get('service_type')}")
                print(f"Amount: {data.get('amount')} {data.get('currency')}")
                print(f"Transit Days: {data.get('estimated_days')}")
                print(f"Valid Until: {data.get('valid_until')}")

                if 'breakdown' in data:
                    print("\nCost Breakdown:")
                    for key, value in data['breakdown'].items():
                        print(f"  {key}: {value}")
            else:
                print(f"❌ Error: {response.text}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

async def main():
    print("="*60)
    print("DHL Quote Testing with New Authentication")
    print("="*60)

    # Test direct API
    await test_direct_dhl_api()

    # Test through carrier service
    await test_carrier_integration_api()

    print("\n" + "="*60)
    print("Testing completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())