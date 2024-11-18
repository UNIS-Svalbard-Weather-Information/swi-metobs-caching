from abc import ABC, abstractmethod
import logging
import json

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
        self.logger = self._setup_logger()
        self._cached_configs = None  # Cache for loaded configurations

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

    def _setup_logger(self):
        """
        Set up a logger for the data source.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _handle_error(self, error):
        """
        Log and handle errors during data fetching or processing.

        Args:
            error (Exception): The exception that occurred.
        """
        self.logger.error(f"Error occurred: {error}")

    def _load_configs_from_files(self, config_files):
        """
        Load configurations from a list of JSON files.

        Args:
            config_files (list): List of file paths to the JSON configuration files.

        Returns:
            list: A combined list of configuration dictionaries from all files.
        """
        if self._cached_configs is not None:
            return self._cached_configs

        configs = []
        for file in config_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    configs.extend(data if isinstance(data, list) else [data])
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self._handle_error(e)

        self._cached_configs = configs
        return configs

    def get_variables(self, station_id, config_files):
        """
        Fetch a mapping of variable identifiers for a station.

        Args:
            station_id (str): The ID of the station.
            config_files (list): List of file paths to configuration files.

        Returns:
            dict: Mapping of variable element IDs to names, or None if not found.
        """
        if not station_id:
            raise ValueError("station_id must be provided")

        configs = self._load_configs_from_files(config_files)
        for config in configs:
            if config.get("id") == station_id:
                return config.get("variables", None)
        return None
