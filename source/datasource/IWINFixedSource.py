from datetime import datetime, timedelta, date
import pandas as pd
import netCDF4 as nc

from .datasource import DataSource


class IWINFixedSource(DataSource):
    def __init__(self):
        super().__init__()

    def fetch_station_data(self, station_id):
        """
        Fetch metadata for a specific station in IWIN project, checking for today's and the previous day's datasets.

        Args:
            station_id (str): The ID of the station to fetch data for.

        Returns:
            dict: Metadata of the NetCDF dataset.
        """
        try:
            # Retrieve the URL pattern from the station's metadata
            metadata = self.config.get_metadata(station_id)
            url_pattern = metadata.get("url")

            # Attempt to load today's dataset
            current_date = date.today()
            dataset_url = current_date.strftime(url_pattern)

            try:
                self.logger.info(f"Attempting to fetch dataset from {dataset_url}")
                dataset = nc.Dataset(dataset_url)
            except FileNotFoundError:
                # If today's dataset is unavailable, try the previous day's dataset
                previous_date = current_date - timedelta(days=1)
                dataset_url = previous_date.strftime(url_pattern)
                self.logger.warning(
                    f"Today's dataset not found. Attempting to fetch previous day's dataset from {dataset_url}")
                dataset = nc.Dataset(dataset_url)  # May raise FileNotFoundError

            # Return dataset metadata as a dictionary
            self.logger.info(f"Dataset successfully loaded from {dataset_url}")
            return {attr: getattr(dataset, attr) for attr in dataset.ncattrs()}

        except FileNotFoundError:
            self.logger.error(f"Dataset not found for station {station_id} on both today and yesterday.")
            raise FileNotFoundError(
                f"Dataset not available for station {station_id} on {current_date} or {previous_date}.")
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching station data for {station_id}: {e}")
            raise RuntimeError(f"An error occurred: {e}")


    def fetch_realtime_data(self, station_id):
        raise NotImplementedError("fetch_realtime_data must be implemented by the subclass.")

    def fetch_timeseries_data(self, station_id, start_time, end_time, return_df=False):
        raise NotImplementedError("fetch_timeseries_data must be implemented by the subclass.")

    def transform_realtime_data(self, raw_data, station_id):
        raise NotImplementedError("transform_realtime_data must be implemented by the subclass.")

    def transform_timeseries_data(self, raw_data, station_id, return_df, resample="60min"):
        raise NotImplementedError("transform_timeseries_data must be implemented by the subclass.")
