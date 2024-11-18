from abc import ABC, abstractmethod
import logging

config_files = [
    "",
    "",
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
        self.logger = self._setup_logger()

    @abstractmethod
    def fetch_station_data(self, station_id):
        """
        Fetch metadata or configuration for a station.

        Args:
            station_id (str): The ID of the station to fetch data for.

        Returns:
            dict: Metadata or configuration for the station.
            None: If the method is not implemented or an error occurs.
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
            None: If the method is not implemented or an error occurs.
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
            None: If the method is not implemented or an error occurs.
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
            None: If the method is not implemented or an error occurs.
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
            None: If the method is not implemented or an error occurs.
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

    def _load_configs_from_files(self, config_file):
        """
        Load configurations from a list of JSON files.

        Args:
            config_files (list): List of file paths to the JSON configuration files.

        Returns:
            list: A combined list of configuration dictionaries from all files.
        """
        configs = []
        for file in config_files:
            with open(file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    configs.extend(data)  # Add the list of configs if the JSON contains a list
                else:
                    configs.append(data)  # Add the single config if the JSON is a dictionary
        return configs

    def get_variables(self, station_id):
        """
        Placeholder method to fetch a mapping of variable identifiers for a station.

        This method should be implemented by subclasses to return a dictionary
        mapping variable element IDs to their human-readable names.

        Args:
            station_id (str): The ID of the station.

        Returns:
            dict: Mapping of variable element IDs to names.
            None: If not implemented.
        """
        configs = self._load_configs_from_files(config_files)
        for config in configs:
            if config.get("id") == station_id:
                return config.get("variables")
        return None





