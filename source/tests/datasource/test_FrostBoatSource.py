import sys
import os

# Dynamically add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from unittest.mock import patch, MagicMock
from source.datasource.FrostBoatSource import FrostBoatSource
import datetime

@pytest.fixture
def frost_source():
    # Setup: Create an instance of FrostBoatSource with a mock API key
    api_key = "mock_api_key"
    return FrostBoatSource(api_key)

def test_fetch_station_data_success_sn77051(frost_source):
    # Mock the response from the API for station SN77051
    mock_response = {
        "data": {
            "id": "SN77051",
            "name": "Station SN77051"
        }
    }

    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # Call the method with station ID SN77051
        result = frost_source.fetch_station_data("SN77051")

        # Assertions
        assert result == mock_response
        # mock_get.assert_called_once()

def test_fetch_realtime_data_success_sn77051(frost_source):
    # Mock the response from the API for station SN77051
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

        # Call the method with station ID SN77051
        result = frost_source.fetch_realtime_data("SN77051")

        # Assertions
        assert result is not None
        # mock_get.assert_called_once()

def test_fetch_realtime_data_failure_sn77046(frost_source):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 404

        # Call the method with station ID SN77046
        result = frost_source.fetch_realtime_data("SN77046")

        # Assertions
        assert result == None

def test_fetch_timeseries_data_success_sn77051(frost_source):
    # Mock the response from the API for station SN77051
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

        # Call the method with station ID SN77051
        result = frost_source.fetch_timeseries_data("SN77051", "2023-10-01T00:00:00Z", "2023-10-01T23:59:59Z")

        # Assertions
        assert result is not None
        # mock_get.assert_called_once()

def test_fetch_timeseries_data_failure_sn77046(frost_source):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 404

        # Call the method with station ID SN77046
        result = frost_source.fetch_timeseries_data("SN77046", "2023-10-01T00:00:00Z", "2023-10-01T23:59:59Z")

        # Assertions
        assert result == {'id': 'SN77046', 'timeseries': []}

def test_is_station_online_true_sn77051(frost_source):
    # Current time in UTC
    current_time = datetime.datetime.now(datetime.timezone.utc)

    # Time 30 minutes ago
    thirty_minutes_ago = current_time - datetime.timedelta(minutes=30)

    # Format the time in ISO 8601 format
    formatted_time = thirty_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Mock the response from the API for station SN77051
    mock_response = {
        "timeseries": [
            {
                "timestamp": formatted_time
            }
        ]
    }

    with patch.object(frost_source, 'fetch_realtime_data') as mock_fetch:
        mock_fetch.return_value = mock_response

        # Call the method with station ID SN77051
        result = frost_source.is_station_online("SN77051")

        # Assertions
        assert result is True


def test_is_station_online_false_time_sn77051(frost_source):
    mock_response = {
        "timeseries": [
            {
                "timestamp": "2023-10-01T12:00:00Z"
            }
        ]
    }

    with patch.object(frost_source, 'fetch_realtime_data') as mock_fetch:
        mock_fetch.return_value = mock_response

        # Call the method with station ID SN77051
        result = frost_source.is_station_online("SN77051")

        # Assertions
        assert result is False

def test_is_station_online_false_sn77046(frost_source):
    with patch.object(frost_source, 'fetch_realtime_data') as mock_fetch:
        mock_fetch.return_value = None

        # Call the method with station ID SN77046
        result = frost_source.is_station_online("SN77046")

        # Assertions
        assert result is False
