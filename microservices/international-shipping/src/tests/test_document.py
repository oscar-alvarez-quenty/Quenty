import pytest
from uuid import uuid4


def generate_document_type_data():
    return {
        "code": f"CODE-{uuid4()}",
        "name": f"Tipo documento {uuid4()}",
        "description": "Documento de prueba automatizada"
    }

def generate_file(name="test.txt", content=b"Contenido de prueba", mime_type="text/plain"):
    return {
        "file": (name, content, mime_type)
    }


@pytest.mark.anyio
async def test_create_document(client_with_auth):
    # Crear tipo de documento
    doc_type_resp = await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())
    doc_type_id = doc_type_resp.json()["id"]

    data = {
        "client_id": "CLIENT_X",
        "user_id": "USER_Y",
        "envio_id": "ENVIO_Z",
        "document_type_id": str(doc_type_id)
    }

    files = generate_file("archivo.txt", b"hola mundo", "text/plain")
    response = await client_with_auth.post("/api/v1/documents/upload", data=data, files=files)
    assert response.status_code == 200
    result = response.json()
    assert "id" in result
    assert result["client_id"] == "CLIENT_X"
    assert result["user_id"] == "USER_Y"
    assert result["envio_id"] == "ENVIO_Z"
    assert result["extension"] == "txt"


@pytest.mark.anyio
async def test_get_document_by_id(client_with_auth):
    doc_type_resp = await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())
    doc_type_id = doc_type_resp.json()["id"]

    files = generate_file("doc_get.pdf", b"content", "application/pdf")
    data = {
        "client_id": "GET_CLIENT",
        "user_id": "GET_USER",
        "envio_id": "GET_ENVIO",
        "document_type_id": str(doc_type_id)
    }

    created = await client_with_auth.post("/api/v1/documents/upload", data=data, files=files)
    doc_id = created.json()["id"]

    response = await client_with_auth.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


@pytest.mark.anyio
async def test_filter_documents(client_with_auth):
    doc_type_resp = await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())
    doc_type_id = doc_type_resp.json()["id"]

    files = generate_file("filter.docx", b"filter content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    data = {
        "client_id": "FILTER_CLIENT",
        "user_id": "FILTER_USER",
        "envio_id": "FILTER_ENVIO",
        "document_type_id": str(doc_type_id)
    }

    await client_with_auth.post("/api/v1/documents/upload", data=data, files=files)

    response = await client_with_auth.get(
        "/api/v1/documents/filter",
        params={
            "client_id": "FILTER_CLIENT",
            "envio_id": "FILTER_ENVIO",
            "document_type_id": doc_type_id
        }
    )

    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1
    for doc in docs:
        assert doc["client_id"] == "FILTER_CLIENT"
        assert doc["envio_id"] == "FILTER_ENVIO"
        assert doc["document_type_id"] == int(doc_type_id)


@pytest.mark.anyio
async def test_delete_document(client_with_auth):
    doc_type_resp = await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())
    doc_type_id = doc_type_resp.json()["id"]

    files = generate_file("to_delete.pdf", b"bye", "application/pdf")
    data = {
        "client_id": "DEL_CLIENT",
        "user_id": "DEL_USER",
        "envio_id": "DEL_ENVIO",
        "document_type_id": str(doc_type_id)
    }

    created = await client_with_auth.post("/api/v1/documents/upload", data=data, files=files)
    doc_id = created.json()["id"]

    response = await client_with_auth.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 204

    get_response = await client_with_auth.get(f"/api/v1/documents/{doc_id}")
    assert get_response.status_code == 404
