import sys
import os

# Dynamically add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from source.datasource.FrostSource import FrostSource
from source.datasource.datasource import DataSource
from source.configHandler.confighandler import ConfigHandler

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

RAW_DATAS_REAL_TIME = {
    "SN99840" : {'data': [{'sourceId': 'SN99840:0',
   'referenceTime': '2024-11-26T16:00:00.000Z',
   'observations': [{'elementId': 'air_temperature',
     'value': -10.6,
     'unit': 'degC'}]},
  {'sourceId': 'SN99840:0',
   'referenceTime': '2024-11-26T16:20:00.000Z',
   'observations': [{'elementId': 'wind_speed',
     'value': 5.8,
     'unit': 'm/s'},
    {'elementId': 'wind_from_direction',
     'value': 54,
     'unit': 'degrees'}]}]},
    "SN99870" : {'data': [{'sourceId': 'SN99870:0',
   'referenceTime': '2024-11-26T16:00:00.000Z',
   'observations': [{'elementId': 'air_temperature',
     'value': -10.5,
     'unit': 'degC'},
    {'elementId': 'wind_speed',
     'value': 4,
     'unit': 'm/s'},
    {'elementId': 'wind_from_direction',
     'value': 257,
     'unit': 'degrees'}]}]}
}

RAW_DATAS_TIME_SERIE = {
'data': [{'sourceId': 'SN99840:0',
   'referenceTime': '2024-12-02T00:00:00.000Z',
   'observations': [{'elementId': 'air_temperature',
     'value': -12.1},
    {'elementId': 'wind_speed',
     'value': 2.6},
    {'elementId': 'wind_speed',
     'value': 2.6}]},
  {'sourceId': 'SN99840:0',
   'referenceTime': '2024-12-02T00:10:00.000Z',
   'observations': [{'elementId': 'wind_speed',
     'value': 3.2}]
   }]
}

@pytest.fixture
def frost_source():
    """Fixture to create a FrostSource instance with a valid client ID."""
    config = ConfigHandler()
    return FrostSource(api_key=config.get_api_credential('FrostSource'))


#@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_fetch_station_data(frost_source, station):
    """Test fetching metadata for a station using the real Frost API."""
    result = frost_source.fetch_station_data(station["id"])

    assert result is not None, f"Failed to fetch data for station {station['id']}"
    assert "data" in result, f"Response missing 'data' field for station {station['id']}"
    print(result)


#@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_fetch_realtime_data(frost_source, station):
    """Test fetching real-time data for a station using the real Frost API."""
    result = frost_source.fetch_realtime_data(station["id"])

    assert result is not None, f"Failed to fetch real-time data for station {station['id']}"
    assert "timeseries" in result, f"Response missing 'timeseries' for station {station['id']}"
    assert len(result["timeseries"]) > 0, f"No observations in real-time data for station {station['id']}"


#@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_fetch_timeseries_data(frost_source, station):
    """Test fetching historical time series data for a station using the real Frost API."""
    start_time = "2023-01-01T00:00:00Z"
    end_time = "2023-01-02T00:00:00Z"

    result = frost_source.fetch_timeseries_data(station["id"], start_time, end_time)

    assert result is not None, f"Failed to fetch time series data for station {station['id']}"
    assert "timeseries" in result, f"Response missing 'timeseries' for station {station['id']}"
    assert len(result["timeseries"]) > 0, f"No observations in time series data for station {station['id']}"


#@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_transform_realtime_data(frost_source, station):
    """Test transforming real-time data for a station."""
    # Fetch real-time raw data
    raw_data = RAW_DATAS_REAL_TIME[station["id"]]

    if raw_data is None:
        pytest.fail(f"No real-time data available for station {station['id']}")

    transformed_data = frost_source.transform_realtime_data(raw_data, station["id"])

    assert transformed_data is not None, f"Failed to transform real-time data for station {station['id']}"
    assert "timeseries" in transformed_data, f"Transformed data missing 'timeseries' for station {station['id']}"
    assert len(transformed_data["timeseries"]) > 0, f"No transformed observations for station {station['id']}"


#@pytest.mark.integration
@pytest.mark.parametrize("station", TEST_STATIONS)
def test_transform_timeseries_data(frost_source, station):
    """Test transforming historical data for a station."""
    # Fetch historical raw data
    start_time = "2023-01-01T00:00:00Z"
    end_time = "2023-01-02T00:00:00Z"
    raw_data = RAW_DATAS_TIME_SERIE

    if raw_data is None:
        pytest.fail(f"No time series data available for station {station['id']}")

    transformed_data = frost_source.transform_timeseries_data(raw_data, station["id"])

    assert transformed_data is not None, f"Failed to transform time series data for station {station['id']}"
    assert "timeseries" in transformed_data, f"Transformed data missing 'timeseries' for station {station['id']}"
    assert len(transformed_data["timeseries"]) > 0, f"No transformed observations for station {station['id']}"
