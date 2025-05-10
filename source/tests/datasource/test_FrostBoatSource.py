import sys
import os

# Dynamically add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from unittest.mock import patch, MagicMock
from source.datasource.FrostBoatSource import FrostBoatSource
@pytest.fixture
def frost_source():
    # Setup: Create an instance of FrostBoatSource with a mock API key
    api_key = "mock_api_key"
    return FrostBoatSource(api_key)

def test_fetch_station_data_success(frost_source):
    # Mock the response from the API
    mock_response = {
        "data": {
            "id": "test_station",
            "name": "Test Station"
        }
    }

    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # Call the method
        result = frost_source.fetch_station_data("test_station")

        # Assertions
        assert result == mock_response
        mock_get.assert_called_once()

def test_fetch_station_data_failure(frost_source):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 404

        # Call the method
        result = frost_source.fetch_station_data("test_station")

        # Assertions
        assert result is None

def test_fetch_realtime_data_success(frost_source):
    # Mock the response from the API
    mock_response = {
        "data": [
            {
                "referenceTime": "2023-10-01T12:00:00Z",
                "observations": [
                    {"elementId": "air_temperature", "value": 15.5}
                ]
            }
        ]
    }

    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # Call the method
        result = frost_source.fetch_realtime_data("test_station")

        # Assertions
        assert result is not None
        mock_get.assert_called_once()

def test_fetch_realtime_data_failure(frost_source):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 404

        # Call the method
        result = frost_source.fetch_realtime_data("test_station")

        # Assertions
        assert result is None

def test_fetch_timeseries_data_success(frost_source):
    # Mock the response from the API
    mock_response = {
        "data": [
            {
                "referenceTime": "2023-10-01T12:00:00Z",
                "observations": [
                    {"elementId": "air_temperature", "value": 15.5}
                ]
            }
        ]
    }

    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # Call the method
        result = frost_source.fetch_timeseries_data("test_station", "2023-10-01T00:00:00Z", "2023-10-01T23:59:59Z")

        # Assertions
        assert result is not None
        mock_get.assert_called_once()

def test_fetch_timeseries_data_failure(frost_source):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 404

        # Call the method
        result = frost_source.fetch_timeseries_data("test_station", "2023-10-01T00:00:00Z", "2023-10-01T23:59:59Z")

        # Assertions
        assert result is None

def test_is_station_online_true(frost_source):
    # Mock the response from the API
    mock_response = {
        "timeseries": [
            {
                "timestamp": "2023-10-01T12:00:00Z"
            }
        ]
    }

    with patch.object(frost_source, 'fetch_realtime_data') as mock_fetch:
        mock_fetch.return_value = mock_response

        # Call the method
        result = frost_source.is_station_online("test_station")

        # Assertions
        assert result is True

def test_is_station_online_false(frost_source):
    with patch.object(frost_source, 'fetch_realtime_data') as mock_fetch:
        mock_fetch.return_value = None

        # Call the method
        result = frost_source.is_station_online("test_station")

        # Assertions
        assert result is False
