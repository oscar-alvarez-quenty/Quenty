import pytest
from uuid import uuid4
from datetime import datetime

def generate_catalog_data():
    return {
        "name": f"Catálogo de prueba {uuid4()}"
    }

def generate_rate_data():
    return {
        "client_id": "1",
        "warehouse_id": "1",
        "operator_id": "OP01",
        "service_id": "SVC01",
        "name": f"Tarifa Test {uuid4()}",
        "weight_min": 0,
        "weight_max": 100,
        "fixed_fee": 20.0,
        "percentage": False
    }

@pytest.mark.anyio
async def test_create_catalog(client_with_auth):
    catalog_data = generate_catalog_data()
    response = await client_with_auth.post("/api/v1/catalogs/create", json=catalog_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == catalog_data["name"]
    assert "id" in data
    assert "created_at" in data

@pytest.mark.anyio
async def test_get_catalog_by_id(client_with_auth):
    # Crear catálogo
    catalog_data = generate_catalog_data()
    created = await client_with_auth.post("/api/v1/catalogs/create", json=catalog_data)
    catalog_id = created.json()["id"]

    # Obtener por ID
    response = await client_with_auth.get(f"/api/v1/catalogs/{catalog_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == catalog_id
    assert data["name"] == catalog_data["name"]

@pytest.mark.anyio
async def test_update_catalog(client_with_auth):
    created = await client_with_auth.post("/api/v1/catalogs/create", json=generate_catalog_data())
    catalog_id = created.json()["id"]

    updated_name = f"Catálogo actualizado {uuid4()}"
    response = await client_with_auth.put(f"/api/v1/catalogs/{catalog_id}", json={"name": updated_name})
    assert response.status_code == 200
    assert response.json()["name"] == updated_name

@pytest.mark.anyio
async def test_list_catalogs(client_with_auth):
    # Crear al menos uno para asegurar que hay resultados
    await client_with_auth.post("/api/v1/catalogs/create", json=generate_catalog_data())

    response = await client_with_auth.post("/api/v1/catalogs/", json={
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
async def test_delete_catalog(client_with_auth):
    created = await client_with_auth.post("/api/v1/catalogs/create", json=generate_catalog_data())
    catalog_id = created.json()["id"]

    response = await client_with_auth.delete(f"/api/v1/catalogs/{catalog_id}")
    assert response.status_code == 204

    # Verifica que ya no exista
    get_response = await client_with_auth.get(f"/api/v1/catalogs/{catalog_id}")
    assert get_response.status_code == 404

@pytest.mark.anyio
async def test_assign_and_remove_rate(client_with_auth):
    # Crear catálogo
    catalog_resp = await client_with_auth.post("/api/v1/catalogs/create", json=generate_catalog_data())
    assert catalog_resp.status_code == 200, catalog_resp.text
    print("CATALOG:", catalog_resp.json())
    catalog_id = catalog_resp.json()["id"]

    # Crear tarifa
    rate_resp = await client_with_auth.post("/api/v1/client-ratebook/", json=generate_rate_data())
    assert rate_resp.status_code == 200, rate_resp.text
    rate_data = rate_resp.json()
    print("RATE CREATED:", rate_data)
    rate_id = rate_data["id"]

    # Asignar tarifa
    print("",catalog_id, rate_id )
    assign_resp = await client_with_auth.post(f"/api/v1/catalogs/{catalog_id}/assign-rate", json={
        "rate_id": rate_id,
        "assign": True
    })
    print("ASSIGN RESPONSE:", assign_resp.status_code, assign_resp.json())
    assert assign_resp.status_code == 200
    assert assign_resp.json()["message"] == "Tarifa asignada correctamente"

    # Verificar asignación
    # assigned_resp = await client_with_auth.get(f"/api/v1/catalogs/{catalog_id}/assigned-rates")
    # print("ASSIGNED RATES:", assigned_resp.status_code, assigned_resp.json())
    # assert assigned_resp.status_code == 200
    # assigned = assigned_resp.json()
    # assert isinstance(assigned, list)
    # assert any(rate["rate"]["id"] == rate_id for rate in assigned)

    # Desasignar tarifa
    unassign_resp = await client_with_auth.post(f"/api/v1/catalogs/{catalog_id}/assign-rate", json={
        "rate_id": rate_id,
        "assign": False
    })
    print("UNASSIGN RESPONSE:", unassign_resp.status_code, unassign_resp.json())
    assert unassign_resp.status_code == 200
    assert unassign_resp.json()["message"] == "Tarifa desasignada correctamente"

    # Verificar que fue removida
    final_resp = await client_with_auth.get(f"/api/v1/catalogs/{catalog_id}/assigned-rates")
    print("FINAL ASSIGNED RATES:", final_resp.status_code, final_resp.json())
    assert all(rate["rate"]["id"] != rate_id for rate in final_resp.json())

