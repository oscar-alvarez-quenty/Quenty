import pytest
from uuid import uuid4

def generate_document_type_data():
    return {
        "code": f"CODE-{uuid4()}",
        "name": f"Tipo documento {uuid4()}",
        "description": "Documento de prueba automatizada"
    }

@pytest.mark.anyio
async def test_create_document_type(client_with_auth):
    data = generate_document_type_data()
    response = await client_with_auth.post("/api/v1/document-types/create", json=data)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["name"] == data["name"]
    assert resp_json["code"] == data["code"]
    assert "id" in resp_json
    assert "created_at" in resp_json

@pytest.mark.anyio
async def test_get_document_type_by_id(client_with_auth):
    data = generate_document_type_data()
    created = await client_with_auth.post("/api/v1/document-types/create", json=data)
    doc_type_id = created.json()["id"]

    response = await client_with_auth.get(f"/api/v1/document-types/{doc_type_id}")
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["id"] == doc_type_id
    assert resp_json["name"] == data["name"]

@pytest.mark.anyio
async def test_update_document_type(client_with_auth):
    created = await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())
    doc_type_id = created.json()["id"]

    new_name = f"Actualizado {uuid4()}"
    response = await client_with_auth.put(f"/api/v1/document-types/{doc_type_id}", json={"name": new_name})
    assert response.status_code == 200
    assert response.json()["name"] == new_name

@pytest.mark.anyio
async def test_list_document_types(client_with_auth):
    await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())

    response = await client_with_auth.post("/api/v1/document-types/", json={
        "start": 0,
        "length": 10,
        "search": {"value": "string"},
        "order": [{"column": 0, "dir": "string"}],
        "columns": [{"data": "string", "name": "string", "searchable": True}]
    })
    assert response.status_code == 200
    data = response.json()
    assert "records_total" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1

@pytest.mark.anyio
async def test_delete_document_type(client_with_auth):
    created = await client_with_auth.post("/api/v1/document-types/create", json=generate_document_type_data())
    doc_type_id = created.json()["id"]

    response = await client_with_auth.delete(f"/api/v1/document-types/{doc_type_id}")
    assert response.status_code == 204

    get_response = await client_with_auth.get(f"/api/v1/document-types/{doc_type_id}")
    assert get_response.status_code == 404
