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

