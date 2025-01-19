from datetime import datetime, timedelta, date
import pandas as pd
import netCDF4 as nc

from .datasource import DataSource


class IWINFixedSource(DataSource):
    def __init__(self, api_key=None):
        super().__init__()

    def fetch_station_data(self, station_id):
        """
        Fetch metadata for a specific station in the IWIN project, checking for today's and the previous day's datasets.

        Args:
            station_id (str): The ID of the station to fetch data for.

        Returns:
            dict: Metadata of the NetCDF dataset.

        Raises:
            FileNotFoundError: If no dataset is available for today or yesterday.
        """
        for days_offset in [0, 1]:  # Check today and yesterday
            try:
                dataset = self._load_file(station_id, old=days_offset)
                self.logger.info(
                    f"Dataset successfully loaded from {station_id} for {'today' if days_offset == 0 else 'yesterday'}")
                return {attr: getattr(dataset, attr) for attr in dataset.ncattrs()}
            except FileNotFoundError:
                self.logger.warning(
                    f"Dataset not found for {station_id} {'today' if days_offset == 0 else 'yesterday'}")

        # If neither today nor yesterday's dataset is available
        error_message = f"Dataset not available for station {station_id} today or yesterday"
        self.logger.error(error_message)
        raise FileNotFoundError(error_message)

    def fetch_realtime_data(self, station_id):
        """
        Fetch the most recent real-time data for a given station.

        Args:
            station_id (str): The ID of the station to fetch real-time data for.

        Returns:
            dict: A dictionary containing the station ID and the most recent real-time data.

        Raises:
            FileNotFoundError: If today's dataset is not available.
            ValueError: If no valid data or variable mappings are found.
        """
        try:
            dataset = self._load_file(station_id, old=0)
        except FileNotFoundError as e:
            self.logger.error(f"Dataset for station {station_id} not found: {e}")
            raise

        variable_map = self.config.get_variable(station_id)
        if not variable_map:
            raise ValueError(f"No variable mappings found for station {station_id}.")
        self.logger.debug(f"Variable mapping for {station_id}: {variable_map}")

        try:
            time_var = dataset.variables["time"]
            times = nc.num2date(time_var[:], time_var.units)
            most_recent_index = len(times) - 1
            most_recent_timestamp = times[most_recent_index]
            self.logger.debug(f"Most recent timestamp for {station_id}: {most_recent_timestamp}")
        except KeyError:
            raise ValueError(f"Time variable not found in dataset for station {station_id}.")
        except Exception as e:
            self.logger.error(f"Error processing time variable for station {station_id}: {e}")
            raise

        raw_data = {}
        for raw_var, mapped_var in variable_map.items():
            if mapped_var and mapped_var in dataset.variables:
                try:
                    # Handle scalar values or numpy arrays
                    value = dataset.variables[mapped_var][most_recent_index]
                    raw_data[raw_var] = value.item() if hasattr(value, "item") else value
                except Exception as e:
                    self.logger.warning(f"Error fetching data for variable {mapped_var} in station {station_id}: {e}")
        self.logger.debug(f"Raw data for {station_id}: {raw_data}")

        transformed_data = self.transform_realtime_data(raw_data, station_id)
        self.logger.debug(f"Transformed data for {station_id}: {transformed_data}")

        return {
            "id": station_id,
            "timeseries": [
                {
                    "timestamp": most_recent_timestamp.isoformat(),
                    **transformed_data,
                }
            ],
        }

    def transform_realtime_data(self, raw_data, station_id):
        """
        Transform raw real-time data using the station's variable mapping.

        Args:
            raw_data (dict): Raw data fetched from the NetCDF dataset.
            station_id (str): The ID of the station.

        Returns:
            dict: Transformed data with mapped variable names and values.

        Raises:
            ValueError: If variable mapping is not valid.
        """
        # Get the variable mapping for the station
        variable_map = self.config.get_variable(station_id)
        if not variable_map:
            raise ValueError(f"No variable mappings found for station {station_id}.")

        # Transform the raw data
        transformed_data = {}
        for raw_key, mapped_var in variable_map.items():
            if mapped_var and raw_key in raw_data:
                transformed_data[raw_key] = raw_data[raw_key]
        self.logger.debug(f"Transformed data after mapping for {station_id}: {transformed_data}")

        return transformed_data

    def fetch_timeseries_data(self, station_id, start_time, end_time, return_df=False):
        raise NotImplementedError("fetch_timeseries_data must be implemented by the subclass.")

    def transform_timeseries_data(self, raw_data, station_id, return_df, resample="60min"):
        raise NotImplementedError("transform_timeseries_data must be implemented by the subclass.")

    def _load_file(self, station_id, old=0):
        """
        Connect to the NetCDF file of the station with a given ID.

        Args:
            station_id (str): ID of the station to retrieve data for.
            old (int): Number of days before the current date. Default is 0 (current day).

        Returns:
            netCDF4.Dataset: The loaded dataset.

        Raises:
            FileNotFoundError: If the dataset is not found.
            ValueError: If the station metadata or URL pattern is invalid.
        """
        # Retrieve station metadata
        metadata = self.config.get_metadata(station_id)
        if not metadata or "url" not in metadata:
            raise ValueError(f"Invalid or missing metadata for station {station_id}")

        url_pattern = metadata.get("url")
        data_date = date.today() - timedelta(days=old)
        dataset_url = data_date.strftime(url_pattern)

        try:
            self.logger.info(f"Attempting to fetch dataset from {dataset_url}")
            dataset = nc.Dataset(dataset_url)
            return dataset
        except FileNotFoundError:
            self.logger.error(f"Dataset not found for station {station_id} on {data_date}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching dataset: {e}")
            raise


