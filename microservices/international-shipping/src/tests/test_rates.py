import pytest

@pytest.mark.anyio
async def test_create_rate(client_with_auth):
    rate_data = {
        "operator_id": "OP01",
        "service_id": "SVC01",
        "name": "Tarifa Test",
        "weight_min": 0.0,
        "weight_max": 100.0,
        "fixed_fee": 25.0,
        "percentage": False
    }

    response = await client_with_auth.post("/api/v1/rates/create", json=rate_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == rate_data["name"]
    assert "id" in data


@pytest.mark.anyio
async def test_get_rate(client_with_auth):
    # Crear tarifa primero
    create_resp = await client_with_auth.post("/api/v1/rates/create", json={
        "operator_id": "OP01",
        "service_id": "SVC02",
        "name": "Tarifa para get",
        "weight_min": 1.0,
        "weight_max": 10.0,
        "fixed_fee": 15.0,
        "percentage": True
    })
    rate = create_resp.json()
    rate_id = rate["id"]

    # Obtener tarifa
    get_resp = await client_with_auth.get(f"/api/v1/rates/{rate_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == rate_id


@pytest.mark.anyio
async def test_list_rates(client_with_auth):
    # Crear algunas tarifas
    for i in range(3):
        await client_with_auth.post("/api/v1/rates/create", json={
            "operator_id": f"OP{i}",
            "service_id": f"SVC{i}",
            "name": f"Tarifa {i}",
            "weight_min": 0.0,
            "weight_max": 50.0,
            "fixed_fee": 10.0 * (i + 1),
            "percentage": False
        })

    request_payload = {
        "start": 0,
        "length": 10,
        "search": {"value": "string"},
        "order": [{"column": 0, "dir": "string"}],
        "columns": [{"data": "string", "name": "string", "searchable": True}]
    }

    response = await client_with_auth.post("/api/v1/rates/", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert data["records_total"] >= 3


@pytest.mark.anyio
async def test_update_rate(client_with_auth):
    # Crear tarifa
    create_resp = await client_with_auth.post("/api/v1/rates/create", json={
        "operator_id": "OP01",
        "service_id": "SVC01",
        "name": "Tarifa original",
        "weight_min": 0.0,
        "weight_max": 20.0,
        "fixed_fee": 10.0,
        "percentage": False
    })
    rate_id = create_resp.json()["id"]

    # Actualizar tarifa
    update_payload = {
        "name": "Tarifa actualizada",
        "fixed_fee": 99.99
    }

    update_resp = await client_with_auth.put(f"/api/v1/rates/{rate_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "Tarifa actualizada"
    assert updated["fixed_fee"] == 99.99


@pytest.mark.anyio
async def test_delete_rate(client_with_auth):
    # Crear tarifa
    create_resp = await client_with_auth.post("/api/v1/rates/create", json={
        "operator_id": "OP03",
        "service_id": "SVC03",
        "name": "Tarifa a eliminar",
        "weight_min": 0.0,
        "weight_max": 100.0,
        "fixed_fee": 50.0,
        "percentage": True
    })
    rate_id = create_resp.json()["id"]

    # Eliminar tarifa
    delete_resp = await client_with_auth.delete(f"/api/v1/rates/{rate_id}")
    assert delete_resp.status_code == 204

    # Verificar que ya no existe
    get_resp = await client_with_auth.get(f"/api/v1/rates/{rate_id}")
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_assign_rate_to_client(client_with_auth):
    # Crear tarifa
    create_resp = await client_with_auth.post("/api/v1/rates/create", json={
        "operator_id": "OP99",
        "service_id": "SVC99",
        "name": "Tarifa asignable",
        "weight_min": 0.0,
        "weight_max": 100.0,
        "fixed_fee": 15.0,
        "percentage": False
    })
    rate_id = create_resp.json()["id"]

    # Asignar a cliente
    assign_payload = {
        "rate_id": rate_id,
        "client_id": 1,
        "warehouse_id": 1
    }

    assign_resp = await client_with_auth.post("/api/v1/rates/assign-to-client", json=assign_payload)
    assert assign_resp.status_code == 200
    assigned = assign_resp.json()
    assert assigned["operator_id"] == "OP99"
