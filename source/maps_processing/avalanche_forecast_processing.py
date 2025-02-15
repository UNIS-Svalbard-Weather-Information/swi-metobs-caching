import sys
import os
import requests
from datetime import datetime, timedelta
from source.logger.logger import Logger

class AvalancheForecastProcessing:
    def __init__(self, n_days_forecast=2, regions_list=None):
        self.logger = Logger.setup_logger('AvalancheForecastProcessing')
        if regions_list is None:
            self.regions_list = ['3001', '3002', '3003', '3004']
        else:
            self.regions_list = regions_list
        self.regions = {region_id: {} for region_id in self.regions_list}
        self.n_days_forecast = n_days_forecast
        self.logger.info("AvalancheForecastProcessing initialized.")

    def fetch_region_data(self, api_url='https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0/api/Region/A'):
        """
        Fetch region data from the API and store it in a dictionary.

        :param api_url: URL of the API to fetch region data
        """
        try:
            self.logger.info(f"Fetching data from API: {api_url}")
            response = requests.get(api_url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            for region in data:
                region_id = str(region['Id'])
                if region_id not in self.regions_list:
                    continue
                name = region['Name']
                polygon = region['Polygon'][0]  # Assuming polygon is a list with one string element

                # Convert polygon string to list of coordinate tuples
                coordinates = [tuple(map(float, coord.split(','))) for coord in polygon.split()]

                self.regions[region_id] = {
                    'name': name,
                    'polygon': coordinates
                }
                self.logger.debug(f"Region {region_id} data processed: {name}")

            self.logger.info("Data fetching and processing completed.")

        except requests.RequestException as e:
            self.logger.error(f"Error fetching data from API: {e}")

    def fetch_forecast_data(self):
        """
        Fetch avalanche forecast data for each region for the next n_days_forecast days.
        """
        today = datetime.now()
        for region_id in self.regions_list:
            start_day = today.strftime("%Y-%m-%d")
            end_day = (today + timedelta(days=self.n_days_forecast)).strftime("%Y-%m-%d")
            api_url = f"https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0/api/AvalancheWarningByRegion/Detail/{region_id}/2/{start_day}/{end_day}"

            try:
                self.logger.info(f"Fetching forecast data for region {region_id} from {api_url}")
                response = requests.get(api_url)
                response.raise_for_status()
                forecast_data = response.json()

                # Initialize forecast dictionary for the region
                self.regions[region_id]['forecast'] = {}

                for forecast in forecast_data:
                    if forecast['IsTendency']:
                        continue  # Skip tendency forecasts

                    forecast_date = datetime.fromisoformat(forecast['ValidFrom']).date()
                    day_key = (forecast_date - today.date()).days

                    # Store only the most recent forecast for each day
                    if day_key not in self.regions[region_id]['forecast'] or \
                            datetime.fromisoformat(forecast['PublishTime']) > \
                            datetime.fromisoformat(self.regions[region_id]['forecast'][day_key]['PublishTime']):

                        self.regions[region_id]['forecast'][day_key] = {
                            "AvalancheProblems": forecast.get("AvalancheProblems"),
                            "AvalancheAdvices": forecast.get("AvalancheAdvices"),
                            "ValidFrom": forecast.get("ValidFrom"),
                            "ValidTo": forecast.get("ValidTo"),
                            "NextWarningTime": forecast.get("NextWarningTime"),
                            "PublishTime": forecast.get("PublishTime"),
                            "DangerLevelName": forecast.get("DangerLevelName"),
                            "MainText": forecast.get("MainText")
                        }

                self.logger.info(f"Forecast data for region {region_id} processed.")

            except requests.RequestException as e:
                self.logger.error(f"Error fetching forecast data for region {region_id}: {e}")

    def get_region(self, region_id):
        """
        Get region information by ID.

        :param region_id: ID of the region
        :return: Dictionary with region name, polygon, and forecast data
        """
        region_info = self.regions.get(region_id, None)
        if region_info:
            self.logger.info(f"Region {region_id} info retrieved: {region_info}")
        else:
            self.logger.warning(f"Region {region_id} not found.")
        return region_info
