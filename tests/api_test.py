import pytest

from src.api import app
from database.db import Session, configure_database
from database.models import Battery

@pytest.fixture(scope="module")
def test_client():
    configure_database("sqlite:///:memory:") # Using in memory db for testing
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def clean_db():
    session = Session()
    session.query(Battery).delete()
    session.commit()
    session.close()

def test_get_all_batteries(test_client):
    batteries = [
        {"capacity_kwh":10, "maximum_power_kw":1},
        {"capacity_kwh":20, "maximum_power_kw":5},
        {"capacity_kwh":30, "maximum_power_kw":10}
    ]

    battery_ids = []
    for battery in batteries:
        post_resp = test_client.post("/", json=battery)
        assert post_resp.status_code == 201
        battery_id = post_resp.get_json()["battery_id"]
        battery_ids.append(battery_id)

    response = test_client.get("/get?limit=2&offset=0")
    assert response.status_code == 200
    data = response.get_json()["batteries"]
    assert len(data) == 2
    assert data[0]["capacity_kwh"] == 10
    assert data[1]["capacity_kwh"] == 20

def test_create_battery(test_client):
    response = test_client.post("/", json={"capacity_kwh": 10, "maximum_power_kw": 5})
    assert response.status_code == 201

    data = response.get_json()
    assert "battery_id" in data
    assert data["capacity_kwh"] == 10
    assert data["maximum_power_kw"] == 5

def test_get_single_battery(test_client):
    response = test_client.post("/", json={"capacity_kwh": 10, "maximum_power_kw": 1})
    assert response.status_code == 201
    battery_id = response.get_json()["battery_id"]

    get_response = test_client.get(f"/{battery_id}")
    assert get_response.status_code == 200
    data = get_response.get_json()
    assert data["capacity_kwh"] == 10
    assert data["maximum_power_kw"] == 1
    assert data["cycles"] == 0
    assert data["state_of_charge"] == "50%"

def test_delete_battery(test_client):
    response = test_client.post("/", json={"capacity_kwh":10, "maximum_power_kw":2})
    assert response.status_code == 201
    battery_id = response.get_json()["battery_id"]

    delete_response = test_client.delete(f"/{battery_id}")
    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.get_json()["message"]

    get_response = test_client.get(f"/{battery_id}")
    assert get_response.status_code == 404

def test_update_battery(test_client):
    response = test_client.post("/", json={"capacity_kwh":10, "maximum_power_kw":1})
    assert response.status_code == 201
    battery_id = response.get_json()["battery_id"]

    update_resp = test_client.patch(f"/update?battery_id={battery_id}&power=1&duration=60")
    assert update_resp.status_code == 200

    data = update_resp.get_json()
    print('data', data)
    assert data["state_of_charge"] == "60%"

def test_get_soc(test_client):
    batteries = [
        {"capacity_kwh":10, "maximum_power_kw":1},
        {"capacity_kwh":10, "maximum_power_kw":5},
        {"capacity_kwh":20, "maximum_power_kw":10}
    ]

    battery_ids = []
    for battery in batteries:
        response = test_client.post("/", json=battery)
        assert response.status_code == 201
        battery_id = response.get_json()["battery_id"]
        battery_ids.append(battery_id)

    get_resp = test_client.get("/soc")
    assert get_resp.status_code == 200

    get_single_resp = test_client.get(f"/soc?battery_id={battery_ids[0]}")
    assert get_single_resp.status_code == 200
    data = get_single_resp.get_json()
    assert data["battery_id"] ==  battery_ids[0]
    assert data["soc"] == 50

def test_get_cycle(test_client):
    batteries = [
        {"capacity_kwh":10, "maximum_power_kw":1},
        {"capacity_kwh":10, "maximum_power_kw":5},
        {"capacity_kwh":20, "maximum_power_kw":10}
    ]

    battery_ids = []
    for battery in batteries:
        response = test_client.post("/", json=battery)
        assert response.status_code == 201
        battery_id = response.get_json()["battery_id"]
        battery_ids.append(battery_id)

    get_resp = test_client.get("/cycles")
    assert get_resp.status_code == 200

    update_resp = test_client.patch(f"/update?battery_id={battery_ids[1]}&power=-1&duration=60")
    assert update_resp.status_code == 200

    get_single_resp = test_client.get(f"/cycles?battery_id={battery_ids[1]}")
    assert get_single_resp.status_code == 200

    data = get_single_resp.get_json()

    assert data["cycles"] == 0.1

def test_create_battery_with_invalid_data(test_client):
    response = test_client.post("/", json={"capacity_kwh": -10, "maximum_power_kw": 0})
    assert response.status_code == 400

    resp = test_client.post("/", json={"maximum_power_kw": -1})
    print('response', resp.get_json())
    assert resp.status_code == 400

def test_update_battery_with_invalid_data(test_client):
    response = test_client.post("/", json={"capacity_kwh":10, "maximum_power_kw":1})
    assert response.status_code == 201
    battery_id = response.get_json()["battery_id"]

    incorrect_duration = test_client.patch(f"/update?battery_id={battery_id}&power=-1&duration=-1")
    print('incorrect_duration', incorrect_duration)
    assert incorrect_duration.status_code == 400

    incorrect_power = test_client.patch(f"/update?battery_id={battery_id}&power=one&duration=60")
    assert incorrect_power.status_code == 400

def test_battery_not_found(test_client):
    get_resp = test_client.get("/1")
    assert get_resp.status_code == 404

    delete_resp = test_client.delete("/1")
    assert delete_resp.status_code == 404

    update_resp = test_client.patch("/update?battery_id=1&power=1&duration=60")
    assert update_resp.status_code == 404

    soc_resp = test_client.get("/soc?battery_id=1")
    assert soc_resp.status_code == 404

    cycle_resp = test_client.get("/cycles?battery_id=1")
    assert cycle_resp.status_code == 404

def test_get_warning(test_client):
    response = test_client.post("/", json={"capacity_kwh":10, "maximum_power_kw":1})
    assert response.status_code == 201
    battery_id = response.get_json()["battery_id"]

    charge_warning = test_client.patch(f"/update?battery_id={battery_id}&power=1&duration=300")
    assert charge_warning.status_code == 200

    discharge_warning = test_client.patch(f"/update?battery_id={battery_id}&power=-1&duration=570")
    assert discharge_warning.status_code == 200
