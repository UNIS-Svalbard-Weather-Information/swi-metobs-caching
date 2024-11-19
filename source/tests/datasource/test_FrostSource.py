import sys
import os

# Dynamically add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import logging
from unittest.mock import patch, Mock
from source.datasource.FrostSource import FrostSource
import json

@pytest.fixture
def frost_source():
    """Fixture to create an instance of FrostSource."""
    return FrostSource(client_id="test_client_id")


@patch("requests.Session.get")
def test_fetch_station_data(mock_get, frost_source):
    """Test fetch_station_data method."""
    # Mock response data
    mock_response = Mock()
    mock_response.json.return_value = {"data": {"id": "123", "name": "Test Station"}}
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Call the method
    result = frost_source.fetch_station_data("123")

    # Assertions
    assert result == {"data": {"id": "123", "name": "Test Station"}}
    mock_get.assert_called_once_with(
        "https://frost.met.no/sources/v0.jsonld", params={"ids": "123"}
    )


@patch("requests.Session.get")
def test_fetch_realtime_data(mock_get, frost_source):
    """Test fetch_realtime_data method."""
    # Mock raw data and transformed data
    mock_raw_data = {
        "data": [
            {
                "referenceTime": "2023-01-01T12:00:00Z",
                "observations": [{"elementId": "air_temperature", "value": 5.2}],
            }
        ]
    }
    mock_transformed_data = {"id": "123", "timeseries": [{"temperature": 5.2, "timestamp": "2023-01-01T12:00:00Z"}]}

    # Mock methods and response
    mock_response = Mock()
    mock_response.json.return_value = mock_raw_data
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    with patch.object(frost_source, "transform_realtime_data", return_value=mock_transformed_data) as mock_transform:
        result = frost_source.fetch_realtime_data("123")

        # Assertions
        assert result == mock_transformed_data
        mock_get.assert_called_once_with(
            "https://frost.met.no/observations/v0.jsonld",
            params={
                "sources": "123",
                "elements": "air_temperature,humidity,wind_speed",
                "referencetime": "latest",
                "maxage": "PT1H",
            },
        )
        mock_transform.assert_called_once_with(mock_raw_data, "123")


@patch("requests.Session.get")
def test_fetch_timeseries_data(mock_get, frost_source):
    """Test fetch_timeseries_data method."""
    # Mock raw data and transformed data
    mock_raw_data = {
        "data": [
            {
                "referenceTime": "2023-01-01T12:00:00Z",
                "observations": [{"elementId": "humidity", "value": 75}],
            }
        ]
    }
    mock_transformed_data = {"id": "123", "timeseries": [{"humidity": 75, "timestamp": "2023-01-01T12:00:00Z"}]}

    # Mock methods and response
    mock_response = Mock()
    mock_response.json.return_value = mock_raw_data
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    with patch.object(frost_source, "transform_timeseries_data", return_value=mock_transformed_data) as mock_transform:
        result = frost_source.fetch_timeseries_data(
            "123", "2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z"
        )

        # Assertions
        assert result == mock_transformed_data
        mock_get.assert_called_once_with(
            "https://frost.met.no/observations/v0.jsonld",
            params={
                "sources": "123",
                "elements": "air_temperature,humidity",
                "referencetime": "2023-01-01T00:00:00Z/2023-01-02T00:00:00Z",
            },
        )
        mock_transform.assert_called_once_with(mock_raw_data, "123")


def test_transform_realtime_data(frost_source):
    """Test transform_realtime_data method."""
    raw_data = {
        "data": [
            {
                "referenceTime": "2023-01-01T12:00:00Z",
                "observations": [{"elementId": "air_temperature", "value": 5.2}],
            }
        ]
    }
    frost_source.get_variable = Mock(return_value={"air_temperature": "temperature"})

    result = frost_source.transform_realtime_data(raw_data, "123")

    assert result == {
        "id": "123",
        "timeseries": [{"temperature": 5.2, "timestamp": "2023-01-01T12:00:00Z"}],
    }


def test_transform_timeseries_data(frost_source):
    """Test transform_timeseries_data method."""
    raw_data = {
        "data": [
            {
                "referenceTime": "2023-01-01T12:00:00Z",
                "observations": [{"elementId": "humidity", "value": 75}],
            }
        ]
    }
    frost_source.get_variable = Mock(return_value={"humidity": "humidity"})

    result = frost_source.transform_timeseries_data(raw_data, "123")

    assert result == {
        "id": "123",
        "timeseries": [{"humidity": 75, "timestamp": "2023-01-01T12:00:00Z"}],
    }
