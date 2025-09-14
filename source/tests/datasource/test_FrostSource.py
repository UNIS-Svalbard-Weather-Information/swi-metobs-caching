import sys
import os
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta, timezone
import pytest
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from source.datasource.FrostSource import FrostSource

@pytest.fixture
def frost_source():
    """
    Fixture to create a FrostSource instance with mocked dependencies.
    """
    client_id = 'test_client_id'
    source = FrostSource(client_id)
    # Mock logger
    source.logger = MagicMock()
    # Mock config
    source.config = MagicMock()
    source.config.get_variable = MagicMock()
    # Mock error handler
    source._handle_error = MagicMock()
    return source

# def test_init():
#     """
#     Test the initialization of FrostSource.
#     """
#     client_id = 'test_client_id'
#     source = FrostSource(client_id)
#     assert source.api_key == client_id
#     assert source.session.auth == (client_id, '')

@patch('requests.Session.get')
def test_fetch_station_data(mock_get, frost_source):
    """
    Test fetching station data successfully.
    """
    station_id = 'SN18700'
    expected_url = f"{frost_source.BASE_URL}/sources/v0.jsonld"
    expected_params = {'ids': station_id}

    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {'data': 'station_data'}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = frost_source.fetch_station_data(station_id)

    mock_get.assert_called_once_with(expected_url, params=expected_params)
    frost_source.logger.info.assert_called_with(f"Fetched station data for {station_id}")
    assert result == {'data': 'station_data'}

@patch('requests.Session.get')
def test_fetch_station_data_error(mock_get, frost_source):
    """
    Test fetching station data with an error response.
    """
    station_id = 'SN18700'
    mock_get.side_effect = requests.exceptions.HTTPError("Error")

    result = frost_source.fetch_station_data(station_id)

    frost_source._handle_error.assert_called_once()
    assert result is None

@patch('requests.Session.get')
def test_fetch_realtime_data(mock_get, frost_source):
    """
    Test fetching real-time data successfully.
    """
    station_id = 'SN18700'
    frost_source.config.get_variable.return_value = {
        'temperature': 'air_temperature',
        'humidity': 'humidity'
    }

    expected_url = f"{frost_source.BASE_URL}/observations/v0.jsonld"
    expected_params = {
        "sources": station_id,
        "elements": "air_temperature,humidity",
        "referencetime": "latest",
        #"maxage": "PT1H"
    }

    mock_response = MagicMock()
    mock_response.json.return_value = {'data': 'realtime_data'}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    frost_source.transform_realtime_data = MagicMock(return_value={'transformed': 'data'})

    result = frost_source.fetch_realtime_data(station_id)

    frost_source.config.get_variable.assert_called_with(station_id)
    mock_get.assert_called_once_with(expected_url, params=expected_params)
    frost_source.transform_realtime_data.assert_called_once_with({'data': 'realtime_data'}, station_id)
    frost_source.logger.info.assert_called_with(f"Fetched real-time data for {station_id}")
    assert result == {'transformed': 'data'}

@patch('requests.Session.get')
def test_fetch_realtime_data_error(mock_get, frost_source):
    """
    Test fetching real-time data with an error response.
    """
    station_id = 'SN18700'
    frost_source.config.get_variable.return_value = {
        'temperature': 'air_temperature',
        'humidity': 'humidity'
    }

    mock_get.side_effect = requests.exceptions.HTTPError("Error")

    result = frost_source.fetch_realtime_data(station_id)

    frost_source._handle_error.assert_called_once()
    assert result is None

@patch('requests.Session.get')
def test_fetch_timeseries_data(mock_get, frost_source):
    """
    Test fetching timeseries data successfully.
    """

    frost_source.config.get_variable.return_value = {
        'airTemperature': 'temperature',
        'humidity': 'humidity'
    }

    station_id = 'SN18700'
    start_time = '2023-01-01T00:00:00Z'
    end_time = '2023-01-01T12:00:00Z'

    expected_url = f"{frost_source.BASE_URL}/observations/v0.jsonld"
    expected_params = {
        "sources": station_id,
        "elements": "temperature,humidity",
        "referencetime": f"{start_time}/{end_time}"
    }

    mock_response = MagicMock()
    mock_response.json.return_value = {'data': 'timeseries_data'}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    frost_source.transform_timeseries_data = MagicMock(return_value={'transformed': 'data'})

    result = frost_source.fetch_timeseries_data(station_id, start_time, end_time)

    mock_get.assert_called_once_with(expected_url, params=expected_params)
    frost_source.transform_timeseries_data.assert_called_once_with({'data': 'timeseries_data'}, station_id, return_df=False)
    frost_source.logger.info.assert_called_with(
        f"Fetched timeseries data for {station_id} from {start_time} to {end_time}"
    )
    assert result == {'transformed': 'data'}

@patch('requests.Session.get')
def test_fetch_timeseries_data_error(mock_get, frost_source):
    """
    Test fetching timeseries data with an error response.
    """
    station_id = 'SN18700'
    start_time = '2023-01-01T00:00:00Z'
    end_time = '2023-01-01T12:00:00Z'

    mock_get.side_effect = requests.exceptions.HTTPError("Error")

    result = frost_source.fetch_timeseries_data(station_id, start_time, end_time)

    frost_source._handle_error.assert_called_once()
    assert result is None

def test_transform_timeseries_data(frost_source):
    """
    Test transforming raw timeseries data.
    """
    raw_data = {
        'data': [
            {
                'referenceTime': '2023-01-01T00:00:00Z',
                'observations': [
                    {'elementId': 'temperature', 'value': 5.0},
                    {'elementId': 'humidity', 'value': 80.0}
                ]
            },
            {
                'referenceTime': '2023-01-01T01:00:00Z',
                'observations': [
                    {'elementId': 'temperature', 'value': 6.0},
                    {'elementId': 'humidity', 'value': 82.0}
                ]
            }
        ]
    }
    station_id = 'SN18700'
    frost_source.config.get_variable.return_value = {
        'airTemperature': 'temperature',
        'humidity': 'humidity'
    }

    result = frost_source.transform_timeseries_data(raw_data, station_id)

    expected_timeseries = [
        {
            'timestamp': '2023-01-01T00:00:00.000Z',
            'airTemperature': 5.0,
            'humidity': 80.0
        },
        {
            'timestamp': '2023-01-01T01:00:00.000Z',
            'airTemperature': 6.0,
            'humidity': 82.0
        }
    ]

    frost_source.logger.info.assert_called_with(
        "Transformed raw time series data into the specified structure dynamically."
    )
    assert result == {'id': station_id, 'timeseries': expected_timeseries}

def test_transform_timeseries_data_error(frost_source):
    """
    Test transforming raw timeseries data with an error.
    """
    raw_data = None
    station_id = 'SN18700'
    frost_source.config.get_variable.side_effect = Exception("Error")

    result = frost_source.transform_timeseries_data(raw_data, station_id)

    frost_source._handle_error.assert_called_once()
    assert result is None

def test_transform_realtime_data(frost_source):
    """
    Test transforming raw real-time data.
    """
    raw_data = {
        'data': [
            {
                'referenceTime': '2023-01-01T01:00:00Z',
                'observations': [
                    {'elementId': 'air_temperature', 'value': 5.0}
                ]
            },
            {
                'referenceTime': '2023-01-01T00:30:00Z',
                'observations': [
                    {'elementId': 'humidity', 'value': 80.0}
                ]
            },
            {
                'referenceTime': '2022-12-31T23:00:00Z',
                'observations': [
                    {'elementId': 'wind_speed', 'value': 10.0}
                ]
            }
        ]
    }
    station_id = 'SN18700'
    frost_source.config.get_variable.return_value = {
        'temperature': 'air_temperature',
        'humidity': 'humidity',
        'wind': 'wind_speed'
    }

    result = frost_source.transform_realtime_data(raw_data, station_id)

    expected_observation = {
        'timestamp': '2023-01-01T01:00:00.000Z',
        'temperature': 5.0,
        'humidity': 80.0
        # 'wind' is excluded because its timestamp is more than 1 hour older than the most recent timestamp
    }

    frost_source.logger.info.assert_called_with(
        "Transformed raw real-time data to include the latest observations within the last hour."
    )
    assert result == {'id': station_id, 'timeseries': [expected_observation]}

def test_transform_realtime_data_error(frost_source):
    """
    Test transforming raw real-time data with an error.
    """
    raw_data = None
    station_id = 'SN18700'
    frost_source.config.get_variable.side_effect = Exception("Error")

    result = frost_source.transform_realtime_data(raw_data, station_id)

    frost_source._handle_error.assert_called_once()
    assert result is None

def test_transform_realtime_data_no_data(frost_source):
    """
    Test transforming raw real-time data when no valid data is found.
    """
    raw_data = {
        'data': [
            {
                'referenceTime': '2023-01-01T01:00:00Z',
                'observations': [
                    {'elementId': 'wind_speed', 'value': 10.0}
                ]
            }
        ]
    }
    station_id = 'SN18700'
    frost_source.config.get_variable.return_value = {
        'temperature': 'air_temperature',
        'humidity': 'humidity'
    }

    result = frost_source.transform_realtime_data(raw_data, station_id)

    frost_source.logger.warning.assert_called_with("No valid data found in real-time observations.")
    assert result is None

def test_is_station_online_recent_data(frost_source):
    """
    Test is_station_online when the latest observation is recent.
    """
    station_id = "SN99857"
    recent_timestamp = (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=30)).isoformat()

    mock_data = {
        "timeseries": [
            {"timestamp": recent_timestamp}
        ]
    }

    with patch.object(frost_source, "fetch_realtime_data", return_value=mock_data):
        assert frost_source.is_station_online(station_id, max_inactive_minutes=120) is True
        frost_source.logger.info.assert_called()


def test_is_station_online_old_data(frost_source):
    """
    Test is_station_online when the latest observation is too old.
    """
    station_id = "SN99857"
    old_timestamp = (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=150)).isoformat()

    mock_data = {
        "timeseries": [
            {"timestamp": old_timestamp}
        ]
    }

    with patch.object(frost_source, "fetch_realtime_data", return_value=mock_data):
        assert frost_source.is_station_online(station_id, max_inactive_minutes=120) is False
        frost_source.logger.info.assert_called()


def test_is_station_online_no_data(frost_source):
    """
    Test is_station_online when no data is returned.
    """
    station_id = "SN99857"

    with patch.object(frost_source, "fetch_realtime_data", return_value=None):
        assert frost_source.is_station_online(station_id, max_inactive_minutes=120) is False
        frost_source.logger.warning.assert_called()


def test_is_station_online_invalid_timestamp(frost_source):
    """
    Test is_station_online when the timestamp is invalid.
    """
    station_id = "SN99857"
    mock_data = {
        "timeseries": [
            {"timestamp": "invalid_timestamp"}
        ]
    }

    with patch.object(frost_source, "fetch_realtime_data", return_value=mock_data):
        assert frost_source.is_station_online(station_id, max_inactive_minutes=120) is False
        frost_source.logger.error.assert_called()
