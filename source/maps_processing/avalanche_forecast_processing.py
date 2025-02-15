import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import requests

from source.logger.logger import Logger

class AvalancheForecastProcessing:
    def __init__(self, n_days_forecast):
        self.logger = Logger.setup_logger('AvalancheForecastProcessing')
        self.regions = {}
        self.logger.info("AvalancheForecastProcessing initialized.")
        self.n_days_forecast = n_days_forecast

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
                region_id = region['Id']
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

    def get_region(self, region_id):
        """
        Get region information by ID.

        :param region_id: ID of the region
        :return: Dictionary with region name and polygon
        """
        region_info = self.regions.get(region_id, None)
        if region_info:
            self.logger.info(f"Region {region_id} info retrieved: {region_info}")
        else:
            self.logger.warning(f"Region {region_id} not found.")
        return region_info