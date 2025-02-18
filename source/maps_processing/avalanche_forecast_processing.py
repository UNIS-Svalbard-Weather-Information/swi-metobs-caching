import sys
import os
import requests
from datetime import datetime, timedelta
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
import numpy as np
from shapely.geometry import mapping, shape
import geojson
import matplotlib.pyplot as plt


from source.logger.logger import Logger
from source.maps_processing.maps_caching import MapsCaching

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
        self.maps_cache = MapsCaching()

    def _binary_to_directions(self, binary_string):
        try:
            # Define the list of directions in order
            directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

            # Ensure the binary string is of length 8
            if len(binary_string) != 8:
                self.logger.error(f"Binary string must be 8 characters long.")
                raise ValueError("Binary string must be 8 characters long.")

            # Create a list of directions based on the binary string
            direction_list = [directions[i] for i in range(8) if binary_string[i] == '1']

            return direction_list
        except Exception as e:
            self.logger.error(f"Error processing binary string: {e}")
            return []

    def _merge_shapefiles(self, shapefile_paths):
        try:
            # Initialize an empty list to store GeoDataFrames
            gdf_list = []

            # Loop through each shapefile path and read it into a GeoDataFrame
            for path in shapefile_paths:
                gdf = gpd.read_file(path)
                gdf_list.append(gdf)

            # Merge all GeoDataFrames into a single GeoDataFrame
            merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))

            return merged_gdf
        except Exception as e:
            self.logger.error(f"Error merging shapefiles: {e}")
            return None

    def _clip_polygons_by_elevation(self, gdf, dem_path, start_height=None, stop_height=None):
        try:
            with rasterio.open(dem_path) as src:
                # Initialize a list to store the clipped geometries
                clipped_geometries = []

                # Loop through each polygon in the GeoDataFrame
                for _, row in gdf.iterrows():
                    geom = row['geometry']

                    # Create a mask for the polygon
                    out_image, out_transform = geometry_mask([geom], transform=src.transform, invert=True, out_shape=src.shape)
                    elevation_data = src.read(1, masked=True)

                    # Mask the elevation data with the polygon
                    masked_elevation = elevation_data * out_image

                    # Create a binary mask for the elevation range
                    if start_height is not None and stop_height is not None:
                        elevation_mask = (masked_elevation >= start_height) & (masked_elevation <= stop_height)
                    elif start_height is not None:
                        elevation_mask = masked_elevation >= start_height
                    elif stop_height is not None:
                        elevation_mask = masked_elevation <= stop_height
                    else:
                        elevation_mask = np.ones(masked_elevation.shape, dtype=bool)

                    # Convert the binary mask to shapes
                    shapes = rasterio.features.shapes(elevation_mask.astype(np.int16), mask=elevation_mask)

                    # Collect the shapes as geometries
                    for shaped, _ in shapes:
                        if shaped:
                            clipped_geom = shape(shaped)
                            clipped_geometries.append(clipped_geom)

                # Create a new GeoDataFrame with the clipped geometries
                clipped_gdf = gpd.GeoDataFrame({'geometry': clipped_geometries}, crs=gdf.crs)
                return clipped_gdf
        except Exception as e:
            self.logger.error(f"Error clipping polygons by elevation: {e}")
            return None

    def _create_geojson_from_dicts(self, gdf_dicts, colormap='viridis'):
        try:
            # Use the specified colormap from matplotlib
            cmap = plt.cm.get_cmap(colormap, len(gdf_dicts))

            features = []
            for i, entry in enumerate(gdf_dicts):
                gdf = entry['gdf']
                label = entry['label']
                description = entry['description']

                # Get a color from the colormap
                color = cmap(i)

                for _, row in gdf.iterrows():
                    geometry = row['geometry']
                    feature = geojson.Feature(
                        geometry=mapping(geometry),
                        properties={
                            'label': label,
                            'description': description,
                            'color': f'#{int(color[0]*255):02X}{int(color[1]*255):02X}{int(color[2]*255):02X}',
                            'fillOpacity': 0.5,
                            'weight': 2,
                        }
                    )
                    features.append(feature)

            feature_collection = geojson.FeatureCollection(features)
            return feature_collection
        except Exception as e:
            self.logger.error(f"Error creating GeoJSON: {e}")
            return None

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
                self.logger.info(f"Fetching forecast data for region {region_id} ({self.regions.get(region_id).get('name', 'Unknown Region')}) from {api_url}")
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
            self.logger.info(f"Region {region_id} info retrieved.")
        else:
            self.logger.warning(f"Region {region_id} not found.")
        return region_info
