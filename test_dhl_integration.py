#!/usr/bin/env python3
"""Test DHL Integration with new API access method"""

import asyncio
import httpx
from datetime import datetime, timedelta

# Test DHL API endpoint
async def test_dhl_rates():
    """Test DHL rates endpoint directly"""

    # DHL Credentials
    USERNAME = "quentysasCO"
    PASSWORD = "M#6bM^7wW!7dV^1n"
    ACCOUNT_NUMBER = "683146118"

    url = "https://express.api.dhl.com/mydhlapi/test/rates"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "customerDetails": {
            "shipperDetails": {
                "postalCode": "760001",
                "cityName": "Cali",
                "countryCode": "CO"
            },
            "receiverDetails": {
                "postalCode": "LIMA 01",
                "cityName": "Lima",
                "countryCode": "PE"
            }
        },
        "accounts": [
            {
                "typeCode": "shipper",
                "number": ACCOUNT_NUMBER
            }
        ],
        "plannedShippingDateAndTime": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT13:00:00GMT+01:00"),
        "unitOfMeasurement": "metric",
        "isCustomsDeclarable": False,
        "packages": [
            {
                "weight": 5,
                "dimensions": {
                    "length": 10,
                    "width": 10,
                    "height": 5
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                auth=(USERNAME, PASSWORD),
                json=payload,
                timeout=30.0
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("\n✅ DHL API Test Successful!")
                print(f"Products available: {len(data.get('products', []))}")

                for product in data.get('products', [])[:3]:
                    print(f"\nService: {product.get('productName')}")
                    if product.get('totalPrice'):
                        price_info = product['totalPrice'][0]
                        print(f"Price: {price_info.get('price')} {price_info.get('currency')}")
            else:
                print(f"\n❌ Error: {response.text}")

        except Exception as e:
            print(f"\n❌ Exception: {str(e)}")

# Test via carrier integration service
async def test_carrier_integration():
    """Test through the carrier integration service"""

    url = "http://localhost:8009/api/v1/quotes"

    payload = {
        "carrier": "DHL",
        "origin": {
            "street": "Calle 1",
            "city": "Cali",
            "state": "Valle del Cauca",
            "postal_code": "760001",
            "country": "CO",
            "contact_name": "Test Shipper",
            "contact_phone": "+573001234567",
            "contact_email": "shipper@test.com"
        },
        "destination": {
            "street": "Av. Arequipa",
            "city": "Lima",
            "state": "Lima",
            "postal_code": "LIMA 01",
            "country": "PE",
            "contact_name": "Test Receiver",
            "contact_phone": "+511234567",
            "contact_email": "receiver@test.com"
        },
        "packages": [
            {
                "weight_kg": 5,
                "length_cm": 10,
                "width_cm": 10,
                "height_cm": 5,
                "description": "Test package"
            }
        ],
        "pickup_date": (datetime.now() + timedelta(days=1)).isoformat()
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=payload,
                timeout=30.0
            )

            print(f"\nCarrier Integration Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ Carrier Integration Test Successful!")
                print(f"Quote ID: {data.get('quote_id')}")
                print(f"Amount: {data.get('amount')} {data.get('currency')}")
                print(f"Service: {data.get('service_type')}")
                print(f"Estimated Days: {data.get('estimated_days')}")
            else:
                print(f"❌ Error: {response.text}")

        except httpx.ConnectError:
            print("❌ Could not connect to carrier integration service on port 8009")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")

async def main():
    print("=" * 60)
    print("Testing DHL Integration with New API Access Method")
    print("=" * 60)

    print("\n1. Testing DHL API directly...")
    print("-" * 40)
    await test_dhl_rates()

    print("\n\n2. Testing via Carrier Integration Service...")
    print("-" * 40)
    await test_carrier_integration()

    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())