import json
from source.logger.logger import Logger

config_files = [
    'static/config/fixed_stations.json',
    'static/config/mobile_stations.json'
]


class ConfigHandler:
    """
    A handler for managing configuration files and providing station-specific data.

    Attributes:
        config_files (list): List of file paths to configuration JSON files.
        _cached_configs (list or None): Cached configuration data, loaded once and reused.
        logger (logging.Logger): Logger instance for logging actions and errors.
    """

    def __init__(self):
        """
        Initialize the ConfigHandler with default configuration files and logger.
        """
        self.config_files = config_files
        self._cached_configs = None
        self.logger = Logger.setup_logger(self.__class__.__name__)

    def get_variable(self, station_id):
        """
        Fetch a mapping of variable identifiers for a specific station.

        Args:
            station_id (str): The ID of the station.

        Returns:
            dict: Mapping of variable element IDs to names, or None if not found.

        Raises:
            ValueError: If `station_id` is not provided.
        """
        if not station_id:
            raise ValueError("station_id must be provided")

        configs = self._load_config()
        for config in configs:
            if config.get("id") == station_id:
                return config.get("variables", None)
        return None

    def get_metadata(self, station_id):
        """
        Fetch metadata for a specific station.

        Args:
            station_id (str): The ID of the station.

        Returns:
            dict: Metadata for the station, or None if not found.

        Raises:
            ValueError: If `station_id` is not provided.
        """
        if not station_id:
            raise ValueError("station_id must be provided")

        configs = self._load_config()
        for config in configs:
            if config.get("id") == station_id:
                return config
        return None

    def get_stations(self, type="all"):
        """
        Get a list of station IDs based on the specified type.

        Args:
            type (str): Type of stations to fetch. Options are:
                - "all": Return all station IDs.
                - "mobile": Return IDs of mobile stations.
                - "fixed": Return IDs of fixed stations.

        Returns:
            list: List of station IDs matching the specified type.

        Raises:
            AssertionError: If `type` is not one of ["all", "mobile", "fixed"].
        """
        assert type in ["all", "mobile", "fixed"], \
            "Type must be one of ['all', 'mobile', 'fixed']"

        configs = self._load_config()
        stations = []
        for config in configs:
            if type == "all" or config.get("type") == type:
                stations.append(config.get("id"))
        return stations

    def _load_config(self):
        """
        Load configurations from a list of JSON files.

        Returns:
            list: A combined list of configuration dictionaries from all files.

        Notes:
            - Caches the configuration data to avoid repeated file I/O.
            - Logs and handles errors such as missing files or invalid JSON.

        Raises:
            FileNotFoundError: If a configuration file is not found.
            json.JSONDecodeError: If a configuration file contains invalid JSON.
        """
        if self._cached_configs is not None:
            return self._cached_configs

        configs = []
        for file in self.config_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    configs.extend(data if isinstance(data, list) else [data])
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self._handle_error(e)

        self._cached_configs = configs
        return configs

    def _handle_error(self, error):
        """
        Log and handle errors that occur during configuration loading or data fetching.

        Args:
            error (Exception): The exception that occurred.
        """
        self.logger.error(f"Error occurred: {error}")
