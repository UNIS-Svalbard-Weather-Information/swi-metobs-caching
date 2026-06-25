import sys
import os
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta, date
import pytest
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from source.datasource.IWINFixedSource import IWINFixedSource

@pytest.fixture
def mock_config_handler():
    """
    Fixture to mock the ConfigHandler used in IWINFixedSource.
    """
    config_handler = MagicMock()
    config_handler.get_metadata.return_value = {
        "url": "https://example.com/datasets/{date}.nc"
    }
    return config_handler


@pytest.fixture
def mock_netcdf_dataset():
    """
    Fixture to mock a NetCDF dataset.
    """
    dataset = MagicMock()
    dataset.ncattrs.return_value = ["attribute1", "attribute2"]
    dataset.attribute1 = "value1"
    dataset.attribute2 = "value2"
    return dataset


@patch("netCDF4.Dataset")
def test_fetch_station_data_today(mock_dataset, mock_config_handler, mock_netcdf_dataset):
    """
    Test fetch_station_data successfully retrieves today's dataset.
    """
    # Mock the Dataset call to return our mock NetCDF dataset
    mock_dataset.return_value = mock_netcdf_dataset

    # Instantiate IWINFixedSource
    datasource = IWINFixedSource()
    datasource.config = mock_config_handler  # Replace the config handler with our mock

    # Call the method under test
    station_id = "station_123"
    result = datasource.fetch_station_data(station_id)

    # Assert the correct dataset was fetched and transformed
    assert result == {
        "attribute1": "value1",
        "attribute2": "value2"
    }
    mock_dataset.assert_called_once_with(date.today().strftime("https://example.com/datasets/{date}.nc"))


@patch("netCDF4.Dataset")
def test_fetch_station_data_not_found(mock_dataset, mock_config_handler):
    """
    Test fetch_station_data raises FileNotFoundError when both today's and yesterday's datasets are unavailable.
    """
    # Mock the Dataset call to raise FileNotFoundError for both days
    mock_dataset.side_effect = FileNotFoundError("Dataset not found.")

    # Instantiate IWINFixedSource
    datasource = IWINFixedSource()
    datasource.config = mock_config_handler  # Replace the config handler with our mock

    # Call the method under test and verify exception is raised
    station_id = "station_123"
    with pytest.raises(FileNotFoundError, match="Dataset not available for station"):
        datasource.fetch_station_data(station_id)

@patch("netCDF4.Dataset")
def test_fetch_realtime_data(mock_dataset, mock_config_handler):
    """
    Test fetch_realtime_data retrieves the most recent real-time data successfully.
    """
    # Mock the dataset variables
    mock_time_var = MagicMock()
    mock_time_var.units = "hours since 2024-12-16 00:00:00"
    mock_time_var.__getitem__.return_value = [0, 1, 2]  # Simulate time indices

    mock_dataset.return_value.variables = {
        "time": mock_time_var,
        "temperature": MagicMock(__getitem__=MagicMock(return_value=-5.3)),
        "wind_speed": MagicMock(__getitem__=MagicMock(return_value=3.2)),
        "wind_direction": MagicMock(__getitem__=MagicMock(return_value=180)),
        "relative_humidity": MagicMock(__getitem__=MagicMock(return_value=85)),
    }

    # Mock the config handler's get_variable method
    mock_config_handler.get_variable.return_value = {
        "airTemperature": "temperature",
        "seaSurfaceTemperature": None,
        "windSpeed": "wind_speed",
        "windDirection": "wind_direction",
        "relativeHumidity": "relative_humidity",
    }

    # Instantiate IWINFixedSource
    datasource = IWINFixedSource()
    datasource.config = mock_config_handler  # Replace the config handler with our mock
    datasource._load_file = MagicMock(return_value=mock_dataset.return_value)  # Mock _load_file

    # Expected output
    expected_output = {
        "id": "bohemanneset",
        "timeseries": [
            {
                "timestamp": "2024-12-16T02:00:00",
                "airTemperature": -5.3,
                "windSpeed": 3.2,
                "windDirection": 180,
                "relativeHumidity": 85,
            }
        ],
    }

    # Call the method under test
    result = datasource.fetch_realtime_data("bohemanneset")

    # Assert the correct data was fetched and transformed
    assert result == expected_output
    datasource._load_file.assert_called_once_with("bohemanneset", old=0)

def test_transform_realtime_data(mock_config_handler):
    """
    Test transform_realtime_data correctly transforms raw data based on variable mappings.
    """
    # Mock raw data
    raw_data = {
        "temperature": -5.3,
        "wind_speed": 3.2,
        "wind_direction": 180,
        "relative_humidity": 85,
    }

    # Mock the config handler's get_variable method
    mock_config_handler.get_variable.return_value = {
        "temperature": "temperature",
        "seaSurfaceTemperature": None,
        "wind_speed": "wind_speed",
        "wind_direction": "wind_direction",
        "relative_humidity": "relative_humidity",
    }

    # Instantiate IWINFixedSource
    datasource = IWINFixedSource()
    datasource.config = mock_config_handler  # Replace the config handler with our mock

    # Call the method under test
    transformed_data = datasource.transform_realtime_data(raw_data, "bohemanneset")

    # Expected transformed data
    expected_transformed_data = {
        "temperature": -5.3,
        "wind_speed": 3.2,
        "wind_direction": 180,
        "relative_humidity": 85,
    }

    # Assert the data was transformed correctly
    assert transformed_data == expected_transformed_data



