import sys
import os

# Dynamically add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from source.datasource.FrostSource import FrostSource
from source.datasource.datasource import DataSource

# Define test data
TEST_STATIONS = [
    {
        "id": "SN99870",
        "name": "ADVENTDALEN",
        "variables": {
            "airTemperature": "air_temperature",
            "seaSurfaceTemperature": None,
            "windSpeed": "wind_speed",
            "windDirection": "wind_from_direction",
            "relativeHumidity": None
        },
        "lat": 78.2022,
        "lon": 15.831,
    },
    {
        "id": "SN99840",
        "name": "SVALBARD LUFTHAVN",
        "variables": {
            "airTemperature": "air_temperature",
            "seaSurfaceTemperature": None,
            "windSpeed": "wind_speed",
            "windDirection": "wind_from_direction",
            "relativeHumidity": None
        },
        "lat": 78.2453,
        "lon": 15.5015,
    }
]

@pytest.fixture
def frost_source():
    """Fixture to create a FrostSource instance with a valid client ID."""
    return FrostSource(client_id="01e39643-4912-4b63-9bbf-26de9e5aa359")


@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_fetch_station_data(frost_source, station):
    """Test fetching metadata for a station using the real Frost API."""
    result = frost_source.fetch_station_data(station["id"])

    assert result is not None, f"Failed to fetch data for station {station['id']}"
    assert "data" in result, f"Response missing 'data' field for station {station['id']}"
    print(result)


@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_fetch_realtime_data(frost_source, station):
    """Test fetching real-time data for a station using the real Frost API."""
    result = frost_source.fetch_realtime_data(station["id"])

    assert result is not None, f"Failed to fetch real-time data for station {station['id']}"
    assert "timeseries" in result, f"Response missing 'timeseries' for station {station['id']}"
    assert len(result["timeseries"]) > 0, f"No observations in real-time data for station {station['id']}"


@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_fetch_timeseries_data(frost_source, station):
    """Test fetching historical time series data for a station using the real Frost API."""
    start_time = "2023-01-01T00:00:00Z"
    end_time = "2023-01-02T00:00:00Z"

    result = frost_source.fetch_timeseries_data(station["id"], start_time, end_time)

    assert result is not None, f"Failed to fetch time series data for station {station['id']}"
    assert "timeseries" in result, f"Response missing 'timeseries' for station {station['id']}"
    assert len(result["timeseries"]) > 0, f"No observations in time series data for station {station['id']}"


@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_transform_realtime_data(frost_source, station):
    """Test transforming real-time data for a station."""
    # Fetch real-time raw data
    raw_data = frost_source.fetch_realtime_data(station["id"])

    if raw_data is None:
        pytest.fail(f"No real-time data available for station {station['id']}")

    transformed_data = frost_source.transform_realtime_data(raw_data, station["id"])

    assert transformed_data is not None, f"Failed to transform real-time data for station {station['id']}"
    assert "timeseries" in transformed_data, f"Transformed data missing 'timeseries' for station {station['id']}"
    assert len(transformed_data["timeseries"]) > 0, f"No transformed observations for station {station['id']}"


@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_transform_timeseries_data(frost_source, station):
    """Test transforming historical data for a station."""
    # Fetch historical raw data
    start_time = "2023-01-01T00:00:00Z"
    end_time = "2023-01-02T00:00:00Z"
    raw_data = frost_source.fetch_timeseries_data(station["id"], start_time, end_time)

    if raw_data is None:
        pytest.fail(f"No time series data available for station {station['id']}")

    transformed_data = frost_source.transform_timeseries_data(raw_data, station["id"])

    assert transformed_data is not None, f"Failed to transform time series data for station {station['id']}"
    assert "timeseries" in transformed_data, f"Transformed data missing 'timeseries' for station {station['id']}"
    assert len(transformed_data["timeseries"]) > 0, f"No transformed observations for station {station['id']}"
