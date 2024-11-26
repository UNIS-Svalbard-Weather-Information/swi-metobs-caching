import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from abc import ABC, abstractmethod
import logging
import json
from source.logger.logger import Logger
from source.confighandler.confighandler import ConfigHandler

config_files = [
    'static/config/fixed_stations.json',
    'static/config/mobile_stations.json'
]


class DataSource(ABC):
    """
    An abstract base class for data sources that fetch and process weather or
    observational data from an external API.

    Attributes:
        api_key (str): API key used for authentication with the data source.
        logger (logging.Logger): Logger for recording actions and errors.
    """

    def __init__(self, api_key=None):
        """
        Initialize the DataSource with an optional API key and set up a logger.

        Args:
            api_key (str, optional): API key for authenticating with the data source.
        """
        self.api_key = api_key
        self.logger = Logger.setup_logger(self.__class__.__name__)
        self.config = ConfigHandler()

    @abstractmethod
    def fetch_station_data(self, station_id):
        """
        Fetch metadata or configuration for a station.

        Args:
            station_id (str): The ID of the station to fetch data for.

        Returns:
            dict: Metadata or configuration for the station.
        """
        pass

    @abstractmethod
    def fetch_realtime_data(self, station_id):
        """
        Retrieve real-time observational data for a specific station.

        Args:
            station_id (str): The ID of the station to fetch real-time data for.

        Returns:
            dict: Transformed real-time data.
        """
        pass

    @abstractmethod
    def fetch_timeseries_data(self, station_id, start_time, end_time):
        """
        Query historical data for a specific station and time range.

        Args:
            station_id (str): The ID of the station to fetch data for.
            start_time (str): The start of the time range in ISO 8601 format.
            end_time (str): The end of the time range in ISO 8601 format.

        Returns:
            dict: Transformed historical data.
        """
        pass

    @abstractmethod
    def transform_realtime_data(self, raw_data, station_id):
        """
        Process and format raw real-time data into a standardized structure.

        Args:
            raw_data (dict): Raw data retrieved from the data source.
            station_id (str): The ID of the station associated with the data.

        Returns:
            dict: Processed and formatted real-time data.
        """
        pass

    @abstractmethod
    def transform_timeseries_data(self, raw_data, station_id):
        """
        Process and format raw historical data into a standardized structure.

        Args:
            raw_data (dict): Raw data retrieved from the data source.
            station_id (str): The ID of the station associated with the data.

        Returns:
            dict: Processed and formatted time series data.
        """
        pass

    def _handle_error(self, error):
        """
        Log and handle errors during data fetching or processing.

        Args:
            error (Exception): The exception that occurred.
        """
        self.logger.error(f"Error occurred: {error}")
