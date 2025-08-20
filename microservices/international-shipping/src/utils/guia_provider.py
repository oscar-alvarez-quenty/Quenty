from datetime import datetime

async def get_data(envio_id: str) -> dict:
    operadores = {
        "servientrega": {
            "shipping_operator": "Servientrega",
            "shipping_service": "Express",
            "payment_type": "Flete por cobrar",
            "estimated_delivery": "2025-08-16",
            "guide": "SRV12345678",
            "barcode": "7501234567890",
        },
        "pasarex": {
            "shipping_operator": "Pasarex",
            "shipping_service": "Estándar",
            "payment_type": "Flete pago",
            "estimated_delivery": "2025-08-15",
            "guide": "PSX98765432",
            "barcode": "7509876543210",
        },
        "dhl": {
            "shipping_operator": "DHL",
            "shipping_service": "Internacional",
            "payment_type": "Flete pago",
            "estimated_delivery": "2025-08-14",
            "guide": "DHL6039760252",
            "barcode": "7501928374650",
        },
        "fedex": {
            "shipping_operator": "FedEx",
            "shipping_service": "Prioritario",
            "payment_type": "Flete por cobrar",
            "estimated_delivery": "2025-08-13",
            "guide": "FDX5647382910",
            "barcode": "7505647382910",
        },
        "deprisa": {
            "shipping_operator": "Deprisa",
            "shipping_service": "Rápido",
            "payment_type": "Flete pago",
            "estimated_delivery": "2025-08-17",
            "guide": "DPR1928374650",
            "barcode": "7501112223334",
        }
    }

    operador_keys = list(operadores.keys())
    operador_key = operador_keys[hash(envio_id) % len(operador_keys)]
    operador_data = operadores[operador_key]

    now = datetime.now()
    recepcion_fecha = now.strftime("%Y-%m-%d")
    recepcion_hora = now.strftime("%H:%M")

    return {
        "shipping_operator": operador_data["shipping_operator"],
        "shipping_service": operador_data["shipping_service"],
        "payment_type": operador_data["payment_type"],
        "fecha_recepcion": recepcion_fecha,
        "hora_recepcion": recepcion_hora,
        "fecha_estimada_entrega": operador_data["estimated_delivery"],
        "no_guide": operador_data["guide"],
        "barcode": operador_data["barcode"],
        "peso_fisico": "2.0 kg",
        "peso_volumetrico": "2.5 kg",
        "pieza": 1,
        "descripcion_contenido": "Documentos legales",
        "destinatario": {
            "nombre": "Carlos Pérez",
            "direccion": "Carrera 45 #78-90, Oficina 3",
            "telefono": "3012345678",
            "pais": "Colombia",
            "ciudad": "Bogotá",
            "codigo_postal": "110111",
            "email": "carlos.perez@email.com",
        },
        "remitente": {
            "nombre": "Quenty S.A.S",
            "direccion": "CARRERA 52 NO. 79-19 LOCAL 11 CENTRO COMERCIAL VERSAILLES",
            "telefono": "3091788",
            "pais": "Colombia",
            "ciudad": "Barranquilla",
            "codigo_postal": "080001",
            "email": "info@quenty.com"
        }
    }
