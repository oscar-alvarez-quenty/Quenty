import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.anyio
async def test_generate_responsibility_letter_pdf_valid(client_with_auth: AsyncClient):
    payload = {
        "envio_id": "TEST-ENVIO-OK",
        "language": "esp"
    }

    response = await client_with_auth.post("/api/v1/letters/responsibility/pdf", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    content = await response.aread()
    assert len(content) > 100  # El PDF no está vacío

@pytest.mark.anyio
async def test_generate_responsibility_letter_invalid_language(client_with_auth: AsyncClient):
    payload = {
        "envio_id": "TEST-ENVIO-FAIL",
        "language": "fr"  # lenguaje no permitido
    }

    response = await client_with_auth.post("/api/v1/letters/responsibility/pdf", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
