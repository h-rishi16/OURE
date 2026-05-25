from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from oure.api.main import app
from oure.api.middleware import require_api_key


def override_require_api_key():
    pass


app.dependency_overrides[require_api_key] = override_require_api_key

client = TestClient(app)


def get_headers():
    return {"X-API-Key": "test-key-123"}


@pytest.mark.req("REQ-OPS-02")
def test_negotiate_low_pc():
    payload = {
        "our_sat_id": "123",
        "their_sat_id": "456",
        "tca": datetime.now(UTC).isoformat(),
        "pc": 1e-7,
        "their_fuel_mass_kg": 20.0,
        "their_maneuver_capability": True,
    }

    response = client.post("/negotiate/", json=payload, headers=get_headers())
    assert response.status_code == 400
    assert "Pc is too low" in response.json()["detail"]


@pytest.mark.req("REQ-OPS-02")
def test_negotiate_no_capability():
    payload = {
        "our_sat_id": "123",
        "their_sat_id": "456",
        "tca": datetime.now(UTC).isoformat(),
        "pc": 1e-4,
        "their_fuel_mass_kg": 20.0,
        "their_maneuver_capability": False,
    }

    response = client.post("/negotiate/", json=payload, headers=get_headers())
    assert response.status_code == 200
    assert response.json()["decision"] == "WE_WILL_MANEUVER"


@pytest.mark.req("REQ-OPS-02")
def test_negotiate_critical_fuel():
    payload = {
        "our_sat_id": "123",
        "their_sat_id": "456",
        "tca": datetime.now(UTC).isoformat(),
        "pc": 1e-4,
        "their_fuel_mass_kg": 2.0,
        "their_maneuver_capability": True,
    }

    response = client.post("/negotiate/", json=payload, headers=get_headers())
    assert response.status_code == 200
    assert response.json()["decision"] == "WE_WILL_MANEUVER"


@pytest.mark.req("REQ-OPS-02")
def test_negotiate_less_fuel():
    # External has more fuel than us (50.0 kg is our assumed nominal)
    payload = {
        "our_sat_id": "123",
        "their_sat_id": "456",
        "tca": datetime.now(UTC).isoformat(),
        "pc": 1e-4,
        "their_fuel_mass_kg": 100.0,
        "their_maneuver_capability": True,
    }

    response = client.post("/negotiate/", json=payload, headers=get_headers())
    assert response.status_code == 200
    assert response.json()["decision"] == "YOU_MUST_MANEUVER"


@pytest.mark.req("REQ-OPS-02")
def test_negotiate_more_fuel():
    # External has less fuel than us (50.0 kg is our assumed nominal)
    payload = {
        "our_sat_id": "123",
        "their_sat_id": "456",
        "tca": datetime.now(UTC).isoformat(),
        "pc": 1e-4,
        "their_fuel_mass_kg": 30.0,
        "their_maneuver_capability": True,
    }

    response = client.post("/negotiate/", json=payload, headers=get_headers())
    assert response.status_code == 200
    assert response.json()["decision"] == "WE_WILL_MANEUVER"
