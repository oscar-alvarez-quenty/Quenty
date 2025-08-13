import pytest
from uuid import uuid4
from src.main import app

def generate_sample_data():
    return {
        "client_id": "1",
        "warehouse_id": "2",
        "operator_id": "OP01",
        "service_id": "SVC01",
        "name": f"Tarifa Básica {uuid4()}",
        "weight_min": 0,
        "weight_max": 100,
        "fixed_fee": 50,
        "percentage": False
    }

@pytest.mark.anyio
async def test_create_rate(client):
    sample_data = generate_sample_data()
    response = await client.post("/api/v1/client-ratebook/", json=sample_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert str(data["client_id"]) == str(sample_data["client_id"])
    assert data["name"] == sample_data["name"]
    assert data["dependent"] is False


@pytest.mark.anyio
async def test_get_rate_by_id(client):
    sample_data = generate_sample_data()
    created = await client.post("/api/v1/client-ratebook/", json=sample_data)
    assert created.status_code == 200
    rate_id = created.json()["id"]

    response = await client.get(f"/api/v1/client-ratebook/detail/{rate_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rate_id


@pytest.mark.anyio
async def test_list_by_client_warehouse(client):
    sample_data = generate_sample_data()
    await client.post("/api/v1/client-ratebook/", json=sample_data)
    response = await client.get(f"/api/v1/client-ratebook/{sample_data['client_id']}/{sample_data['warehouse_id']}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.anyio
async def test_match_exact(client):
    sample_data = generate_sample_data()
    await client.post("/api/v1/client-ratebook/", json=sample_data)

    response = await client.post("/api/v1/client-ratebook/match", json={
        "client_id": str(sample_data["client_id"]),
        "warehouse_id": str(sample_data["warehouse_id"]),
        "operator_id": sample_data["operator_id"],
        "service_id": sample_data["service_id"],
        "weight": 50
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == sample_data["name"]


@pytest.mark.anyio
async def test_match_default(client):
    response = await client.post("/api/v1/client-ratebook/match", json={
        "client_id": "999",
        "warehouse_id": "999",
        "operator_id": "X",
        "service_id": "Y",
        "weight": 10
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 0
    assert data["name"] == "Tarifa por defecto"
    assert data["fixed_fee"] == 30


@pytest.mark.anyio
async def test_update_rate(client):
    sample_data = generate_sample_data()
    created = await client.post("/api/v1/client-ratebook/", json=sample_data)
    assert created.status_code == 200
    rate_id = created.json()["id"]

    updated_data = {
        "fixed_fee": 99.9
    }

    response = await client.put(f"/api/v1/client-ratebook/{rate_id}", json=updated_data)
    assert response.status_code == 200, response.text
    assert response.json()["fixed_fee"] == 99.9


@pytest.mark.anyio
async def test_soft_delete(client):
    sample_data = generate_sample_data()
    created = await client.post("/api/v1/client-ratebook/", json=sample_data)
    rate_id = created.json()["id"]

    response = await client.delete(f"/api/v1/client-ratebook/{rate_id}")
    assert response.status_code == 204

    # Verifica que ya no aparece
    list_response = await client.get(f"/api/v1/client-ratebook/{sample_data['client_id']}/{sample_data['warehouse_id']}")
    assert all(rate["id"] != rate_id for rate in list_response.json())
