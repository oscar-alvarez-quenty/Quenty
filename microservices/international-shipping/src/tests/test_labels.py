import pytest
from fastapi import status

@pytest.mark.anyio
async def test_generate_labels_endpoint(client_with_auth):
    # Datos de prueba
    payload = {
        "envio_ids": [101, 102, 103],
        "format_type": 1
    }

    # Llamada al endpoint
    response = await client_with_auth.post("/api/v1/labels/generate-labels", json=payload)

    # Verificaciones
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=labels.pdf"
    assert response.content.startswith(b"%PDF")
