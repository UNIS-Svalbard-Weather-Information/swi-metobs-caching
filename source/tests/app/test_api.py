import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import json


def test_online_stations(client):
    """Test the /api/station/online endpoint."""
    response = client.get("/api/station/online")

    assert response.status_code == 200

    data = response.get_json()

    expected_data = {
        "online_stations": [
            {
                "id": "SN99895",
                "location": {"lat": 78.9633, "lon": 11.3475},
                "name": "KVADEHUKEN II",
                "type": "Unknown"
            },
            {
                "id": "SN99763",
                "location": {"lat": 78.0648, "lon": 17.0442},
                "name": "REINDALSPASSET",
                "type": "Unknown"
            }
        ]
    }

    assert data == expected_data  # Ensure response matches the expected format


def test_offline_stations(client):
    """Test the /api/station/offline endpoint."""
    response = client.get("/api/station/offline")

    assert response.status_code == 200

    data = response.get_json()

    expected_data = {
        "offline_stations": [
            {
                "id": "SN99885",
                "location": {"lat": 78.38166, "lon": 14.753},
                "name": "Bohemanneset",
                "type": "Unknown"
            },
            {
                "id": "daudmannsodden",
                "location": {"lat": 78.21056, "lon": 12.98685},
                "name": "Daudmannsodden",
                "type": "Unknown"
            }
        ]
    }

    assert data == expected_data  # Ensure response matches the expected format


def test_station_metadata(client):
    """Test the /station/<station_id> endpoint."""
    station_id = "12345"
    response = client.get(f"/api/station/{station_id}")

    assert response.status_code == 200
    expected_data = {
        "id": "12345",
        "location": {"lat": 78.5, "lon": 15.0},
        "name": "Mock Station 12345",
        "type": "MockType"
    }
    assert response.get_json() == expected_data

def test_station_metadata_not_found(client):
    """Test the /station/<station_id> endpoint for an unknown station."""
    station_id = "99999"
    response = client.get(f"/api/station/{station_id}")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Station not found"

def test_realtime_data(client):
    """Test the /station-data/<station_id>?data=now endpoint."""
    station_id = "12345"
    response = client.get(f"/api/station-data/{station_id}?data=now")

    assert response.status_code == 200
    expected_data = {
        "temperature": -5.0,
        "wind_speed": 10.5,
        "pressure": 1015
    }
    assert response.get_json() == expected_data

def test_realtime_data_not_found(client):
    """Test the /station-data/<station_id>?data=now endpoint for missing data."""
    station_id = "99999"
    response = client.get(f"/api/station-data/{station_id}?data=now")

    assert response.status_code == 404
    assert response.get_json()["error"] == "No real-time data available"

def test_realtime_data_invalid_request(client):
    """Test the /station-data/<station_id> with invalid query parameters."""
    station_id = "12345"
    response = client.get(f"/api/station-data/{station_id}")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid request"


def test_realtime_data_invalid_request(client):
    """Test the /station-data/<station_id> with invalid query parameters."""
    station_id = "12345"
    response = client.get(f"/api/station-data/{station_id}")
    assert response.status_code == 400
    assert response.json["error"] == "Invalid request"
