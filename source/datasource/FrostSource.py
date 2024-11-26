import requests
from nbclient.client import timestamp
from datetime import datetime, timedelta

from .datasource import DataSource

class FrostSource(DataSource):
    """
    A data source integration for the Frost API provided by MET Norway.
    This class allows fetching metadata, real-time, and historical weather data
    from specific weather stations.

    Attributes:
        BASE_URL (str): The base URL for the Frost API.
        session (requests.Session): A session object for making authenticated API requests.
    """

    BASE_URL = "https://frost.met.no"

    def __init__(self, client_id):
        """
        Initialize the FrostSource instance with the given client ID.

        Args:
            client_id (str): The client ID for authenticating with the Frost API.
        """
        super().__init__(api_key=client_id)
        self.session = requests.Session()
        self.session.auth = (self.api_key, '')

    def fetch_station_data(self, station_id):
        """
        Fetch metadata for a specific station.

        Args:
            station_id (str): The ID of the weather station.

        Returns:
            dict: A dictionary containing station metadata if successful.
            None: If an error occurs during the request.
        """
        endpoint = f"{self.BASE_URL}/sources/v0.jsonld"
        params = {"ids": station_id}
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Fetched station data for {station_id}")
            return data
        except requests.exceptions.RequestException as e:
            self._handle_error(e)
            return None

    def fetch_realtime_data(self, station_id):
        """
        Retrieve real-time weather data for a specific station.

        Args:
            station_id (str): The ID of the weather station.

        Returns:
            dict: A dictionary containing transformed real-time weather data if successful.
            None: If an error occurs during the request.
        """
        endpoint = f"{self.BASE_URL}/observations/v0.jsonld"

        stations_variable = self.config.get_variable(station_id)
        variables = []
        for var in stations_variable:
            if not (stations_variable[var] == None):
                variables.append(stations_variable[var])

        params = {
            "sources": station_id,
            "elements": ",".join(variables),
            "referencetime": "latest",
            "maxage": "PT1H"  # Last hour
        }

        #print(params)
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            raw_data = response.json()
            self.logger.info(f"Fetched real-time data for {station_id}")
            return self.transform_realtime_data(raw_data, station_id)
        except requests.exceptions.RequestException as e:
            self._handle_error(e)
            return None

    def fetch_timeseries_data(self, station_id, start_time, end_time):
        """
        Query historical weather data for a specific time range.

        Args:
            station_id (str): The ID of the weather station.
            start_time (str): The start time for the query in ISO 8601 format.
            end_time (str): The end time for the query in ISO 8601 format.

        Returns:
            dict: A dictionary containing transformed historical weather data if successful.
            None: If an error occurs during the request.
        """
        endpoint = f"{self.BASE_URL}/observations/v0.jsonld"
        params = {
            "sources": station_id,
            "elements": "air_temperature,humidity",
            "referencetime": f"{start_time}/{end_time}"
        }
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            raw_data = response.json()
            self.logger.info(f"Fetched timeseries data for {station_id} from {start_time} to {end_time}")
            return self.transform_timeseries_data(raw_data, station_id)
        except requests.exceptions.RequestException as e:
            self._handle_error(e)
            return None

    def transform_timeseries_data(self, raw_data, station_id):
        """
        Transform raw historical data into a time series format.

        Args:
            raw_data (dict): Raw data retrieved from the Frost API.
            station_id (str): The ID of the weather station.

        Returns:
            dict: Transformed data containing a list of timestamped observations.
            None: If an error occurs during transformation.
        """
        try:
            variable_mapping = self.config.get_variable(station_id)
            observations = raw_data.get('data', [])
            timeseries = []

            for item in observations:
                timestamp = item.get('referenceTime')
                observation_data = {}
                for obs in item.get('observations', []):
                    variable_name = variable_mapping.get(obs.get('elementId'))
                    if variable_name:
                        observation_data[variable_name] = obs.get('value')
                if observation_data:
                    observation_data["timestamp"] = timestamp
                    timeseries.append(observation_data)

            self.logger.info("Transformed raw time series data into the specified structure dynamically.")
            return {
                "id": station_id,
                "timeseries": timeseries
            }
        except Exception as e:
            self._handle_error(e)
            return None

    def transform_realtime_data(self, raw_data, station_id):
        """
        Transform raw real-time data into a structured format.

        Args:
            raw_data (dict): Raw data retrieved from the Frost API.
            station_id (str): The ID of the weather station.

        Returns:
            dict: Transformed data containing the latest observation.
            None: If an error occurs during transformation or if no valid data is found.
        """
        try:
            variable_mapping = self.config.get_variable(station_id)
            sources = raw_data.get('data', [])

            # Initialize the latest observation with no timestamp
            latest_observation = {"timestamp": None}
            all_observations = {}

            for source in sources:
                # Parse the source timestamp into a timezone-aware datetime object
                source_timestamp = datetime.fromisoformat(source.get('referenceTime').replace('Z', '+00:00'))

                # Check if this is the most recent timestamp
                if latest_observation["timestamp"] is None or source_timestamp > latest_observation["timestamp"]:
                    latest_observation["timestamp"] = source_timestamp

                # Collect all observations
                for obs in source.get('observations', []):
                    var = next((k for k, v in variable_mapping.items() if v == obs.get('elementId')), None)
                    if var is not None:  # Ensure variable exists in mapping
                        # Store the observation with its timestamp
                        all_observations[var] = (source_timestamp, obs.get('value'))

            # Consolidate all observations from the past hour
            threshold_time = latest_observation["timestamp"] - timedelta(hours=1)
            consolidated_observations = {}

            for var, (timestamp, value) in all_observations.items():
                if timestamp >= threshold_time:  # Include observations within the 1-hour window
                    consolidated_observations[var] = value

            # Update the latest observation dictionary
            latest_observation.update(consolidated_observations)

            # Set the timestamp of the consolidated observation to the most recent timestamp
            latest_observation["timestamp"] = latest_observation["timestamp"].strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            if latest_observation:
                self.logger.info("Transformed raw real-time data to include only the latest observation.")
                return {
                    "id": station_id,
                    "timeseries": [latest_observation]  # Wrap in a list for consistency
                }
            else:
                self.logger.warning("No valid data found in real-time observations.")
                return None
        except Exception as e:
            self._handle_error(e)
            return None
