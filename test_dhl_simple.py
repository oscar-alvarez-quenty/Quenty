#!/usr/bin/env python3
"""Simple DHL test with exact working payload"""

import httpx
import asyncio
import json
from datetime import datetime, timedelta

async def test_dhl():
    USERNAME = "quentysasCO"
    PASSWORD = "M#6bM^7wW!7dV^1n"

    url = "https://express.api.dhl.com/mydhlapi/test/rates"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Use exact payload that worked before
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
                "number": "683146118"
            }
        ],
        "plannedShippingDateAndTime": "2025-09-15T13:00:00GMT+01:00",
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
        print("Testing DHL API with simple payload...")
        print("=" * 60)

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
            print(f"✅ Success! Products: {len(data.get('products', []))}")

            for product in data.get('products', []):
                print(f"\n📦 Service: {product.get('productName')}")
                if 'totalPrice' in product and product['totalPrice']:
                    prices = product['totalPrice']
                    for price in prices:
                        print(f"   💰 Price: {price.get('price')} {price.get('currency')}")
                        if 'priceCurrency' in price:
                            print(f"   💱 Currency: {price.get('priceCurrency')}")

                # Show delivery info
                if 'deliveryCapabilities' in product:
                    delivery = product['deliveryCapabilities']
                    if 'totalTransitDays' in delivery:
                        print(f"   🚚 Transit Days: {delivery['totalTransitDays']}")
                    if 'estimatedDeliveryDateAndTime' in delivery:
                        print(f"   📅 Estimated Delivery: {delivery['estimatedDeliveryDateAndTime']}")

            # Print raw response for debugging
            print("\n" + "=" * 60)
            print("Raw response (first product):")
            if data.get('products'):
                print(json.dumps(data['products'][0], indent=2))
        else:
            print(f"❌ Error: {response.text}")

asyncio.run(test_dhl())