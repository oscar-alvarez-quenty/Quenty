import pytest
from httpx import AsyncClient
from fastapi import status
from io import BytesIO

# PNG mínimo válido (1x1 px transparente)
MINIMAL_PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    b'\x00\x00\x00\nIDATx\xdac`\x00\x00\x00\x02\x00\x01'
    b'\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'
)

@pytest.mark.anyio
async def test_upload_signature_png_valid(client: AsyncClient):
    fake_png_file = BytesIO(MINIMAL_PNG_BYTES)
    files = {"image": ("signature.png", fake_png_file, "image/png")}
    data = {"client_id": "test-client-123"}

    response = await client.post("/api/v1/signatures/", data=data, files=files)

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["client_id"] == data["client_id"]
    assert json_data["image_base64"].startswith("data:image/png;base64,")


@pytest.mark.anyio
async def test_upload_signature_invalid_format(client: AsyncClient):
    # Enviamos un archivo JPEG falso
    fake_jpeg = BytesIO(b"this-is-not-a-png")
    files = {"image": ("signature.jpeg", fake_jpeg, "image/jpeg")}
    data = {"client_id": "test-client-456"}

    response = await client.post("/api/v1/signatures/", data=data, files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Only PNG images are allowed"
