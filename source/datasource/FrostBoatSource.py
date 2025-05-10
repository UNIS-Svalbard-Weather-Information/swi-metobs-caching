# SPDX-FileCopyrightText: 2025 Louis Pauchet <louis.pauchet@insa-rouen.fr>
# SPDX-License-Identifier:  CC0-1.0


import requests
from datetime import datetime, timedelta, timezone
import pandas as pd
import traceback

from .datasource import DataSource


class FrostBoatSource(DataSource):
    """
    A data source integration for the boats from Frost API provided by MET Norway.
    This class allows fetching metadata, real-time, and historical weather data
    from specific weather stations.

    Attributes:
        BASE_URL (str): The base URL for the Frost API.
        session (requests.Session): A session object for making authenticated API requests.
    """

    BASE_URL = "https://frost.met.no"

    def __init__(self, api_key):
        """
        Initialize the FrostSource instance with the given client ID.

        Args:
            client_id (str): The client ID for authenticating with the Frost API.
        """
        super().__init__(api_key=api_key)
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
        variables = ['latitude','longitude']
        for var in stations_variable:
            if stations_variable[var] is not None:
                variables.append(stations_variable[var])

        params = {
            "sources": station_id,
            "elements": ",".join(variables),
            "referencetime": "latest",
            #"maxage": "PT1H"  # Last hour
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

    def fetch_timeseries_data(self, station_id, start_time, end_time, return_df = False):
        """
        Query historical weather data for a specific time range.

        Args:
            return_df: Return the data as a dictionary for API response or pandas dataframe.
            station_id (str): The ID of the weather station.
            start_time (str): The start time for the query in ISO 8601 format.
            end_time (str): The end time for the query in ISO 8601 format.

        Returns:
            dict: A dictionary containing transformed historical weather data if successful.
            None: If an error occurs during the request.
        """
        endpoint = f"{self.BASE_URL}/observations/v0.jsonld"

        stations_variable = self.config.get_variable(station_id)
        variables = ['latitude', 'longitude']
        for var in stations_variable:
            if stations_variable[var] is not None:
                variables.append(stations_variable[var])

        params = {
            "sources": station_id,
            "elements": ",".join(variables),
            "referencetime": f"{start_time}/{end_time}"
        }
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            raw_data = response.json()
            self.logger.info(f"Fetched timeseries data for {station_id} from {start_time} to {end_time}")
            return self.transform_timeseries_data(raw_data, station_id, return_df = return_df)
        except requests.exceptions.RequestException as e:
            self._handle_error(e)
            return None

    def transform_timeseries_data(self, raw_data, station_id, return_df=False, resample='60min'):
        """
        Transform raw historical data into a time series format.

        Args:
            return_df (bool): Should a DataFrame be returned instead of raw data.
            resample (str): Resampling interval for the data (e.g., '30min', '1H'), default = '60min'.
            raw_data (dict): Raw data retrieved from the Frost API.
            station_id (str): The ID of the weather station.

        Returns:
            dict: Transformed data containing a list of timestamped observations.
            pd.DataFrame: DataFrame with resampled and transformed data if `return_df` is True.
            None: If an error occurs during transformation.
        """
        try:
            # Fetch variable mapping for the station
            variable_mapping = self.config.get_variable(station_id)
            observations = raw_data.get('data', [])
            timeseries = []

            for source in observations:
                # Initialize a dictionary for each timestamp
                record = {"timestamp": source.get('referenceTime')}
                for obs in source.get('observations', []):
                    element_id = obs.get('elementId')
                    variable_name = next((k for k, v in variable_mapping.items() if v == element_id), None)

                    if element_id == 'latitude':
                        record['latitude'] = obs.get('value')
                        continue

                    if element_id == 'longitude':
                        record['longitude'] = obs.get('value')
                        continue

                    if variable_name:
                        record[variable_name] = obs.get('value')
                
                timeseries.append(record)

            # Create DataFrame from the timeseries data
            df = pd.DataFrame(timeseries)

            # Ensure 'timestamp' is parsed as datetime
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)

            # Resample if required
            if resample != "AUTO" and not df.empty:
                df = df.resample('10min').mean().resample(resample).first()
                df.dropna(inplace=True)

            # Return DataFrame or raw timeseries list
            if return_df:
                return df

            self.logger.info("Transformed raw time series data into the specified structure dynamically.")
            return {
                "id": station_id,
                "timeseries": self.df_to_timeserie(df)
            }

        except Exception as e:
            self._handle_error(e)
            traceback.print_exc()
            return None

    def transform_realtime_data(self, raw_data, station_id):
        """
        Transform raw real-time data into a structured format.

        Args:
            raw_data (dict): Raw data retrieved from the Frost API.
            station_id (str): The ID of the weather station.

        Returns:
            dict: Transformed data containing the latest observation for each variable.
            None: If an error occurs during transformation or if no valid data is found.
        """
        try:
            variable_mapping = self.config.get_variable(station_id)
            sources = raw_data.get('data', [])

            latest_observations = {}

            if len(sources) == 1:
                lat, long = None, None
                source = sources[0]
                source_timestamp = datetime.fromisoformat(source.get('referenceTime').replace('Z', '+00:00'))
                observation = {'timestamp': source_timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'}
                
                for obs in source.get('observations', []):
                        element_id = obs.get('elementId')
                        value = obs.get('value')
                        #print(element_id)
                        if element_id == 'latitude':
                            lat = value

                        if element_id == 'longitude':
                            long = value

                        var = next((k for k, v in variable_mapping.items() if v == element_id), None)

                        if var is not None:
                            observation[var] = value

                if lat and long:
                    observation["location"] = {"lat": lat, "lon": long}

                return {
                    "id": station_id,
                    "timeseries": [observation]
                }
            
            else:
                return None


        except Exception as e:
            self._handle_error(e)
            return None

    def is_station_online(self, station_id, max_inactive_minutes=120):
        """
        Determine whether a given station is 'online' by checking the timestamp of
        its most recent real-time observation. If the latest data is less than
        `max_age_hours` old, the station is considered online.

        Args:
            station_id (str): The ID of the weather station.
            max_age_hours (int): Maximum age (in hours) of the latest observation
                                 to still consider the station 'online'.

        Returns:
            bool: True if the station is considered online, False otherwise.
        """
        data = self.fetch_realtime_data(station_id)
        if not data:
            self.logger.warning(f"No data returned for station {station_id}.")
            self.logger.info(f"Station {station_id} is considered OFFLINE.")
            return False

        #print(data)

        # Check if the data structure is as expected
        timeseries = data.get("timeseries")
        if not timeseries or len(timeseries) == 0:
            self.logger.warning(f"No timeseries entries for station {station_id}.")
            self.logger.info(f"Station {station_id} is considered OFFLINE.")
            return False

        # We'll take the first (and presumably most recent) timeseries entry
        latest_entry = timeseries[0]
        timestamp_str = latest_entry.get("timestamp")
        if not timestamp_str:
            self.logger.warning(f"No 'timestamp' field for station {station_id}.")
            self.logger.info(f"Station {station_id} is considered OFFLINE.")
            return False

        # Convert to Python datetime; handle trailing "Z" by replacing with UTC offset.
        try:
            latest_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError as e:
            self.logger.error(f"Error parsing timestamp for station {station_id}: {e}")
            return False

        # Define the cutoff time
        cutoff_time = datetime.utcnow().replace(tzinfo=timezone.utc)  - timedelta(minutes=max_inactive_minutes)

        # If the station reported data newer than the cutoff, it's "online"
        if latest_time >= cutoff_time:
            self.logger.info(
                f"Station {station_id} last timestamp = {latest_time} (< {max_inactive_minutes}min old). Considered ONLINE."
            )
            return True
        else:
            self.logger.info(
                f"Station {station_id} last timestamp = {latest_time}, older than {max_inactive_minutes}min. OFFLINE."
            )
            return False