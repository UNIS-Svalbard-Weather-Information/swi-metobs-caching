import sys
import os
import requests
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import mapping, Polygon, MultiPolygon
from shapely.ops import transform
import geojson
import matplotlib.pyplot as plt
import json
import traceback
from pyproj import CRS, Transformer
import urllib.parse


from source.logger.logger import Logger
from source.maps_processing.maps_caching import MapsCaching


class AvalancheForecastProcessing:

    """
    A class to process and visualize avalanche forecast data for specified regions.

    This class fetches avalanche forecast data from an API, processes it to create GeoJSON layers,
    and saves these layers as files. It handles region-specific data, including forecast details
    and geographic information, and uses this data to generate visual representations of avalanche risks.

    Attributes:
        logger (Logger): Logger instance for logging messages.
        regions_list (list): List of region IDs to process.
        regions (dict): Dictionary storing region data, including names and polygons.
        n_days_forecast (int): Number of days to forecast.
        maps_cache (MapsCaching): Instance of MapsCaching for managing map data.
        export_directory (str): Directory where processed GeoJSON files are saved.

    Methods:
        __init__(n_days_forecast=1, regions_list=None):
            Initializes the AvalancheForecastProcessing instance with the specified number of forecast days
            and a list of region IDs.

        _binary_to_directions(binary_string):
            Converts a binary string to a list of cardinal and intercardinal directions.

        _create_geojson_from_dicts(gdf_dicts, colormap='viridis'):
            Creates a GeoJSON FeatureCollection from a list of GeoDataFrame dictionaries, applying a colormap.

        _save_geojson_to_file(geojson_obj, file_name):
            Saves a GeoJSON object to a file in the export directory.

        clip_shapefile_with_gps_contour(gps_coordinates, shapefile_path):
            Clips a shapefile using a contour defined by a list of GPS coordinates.

        fetch_region_data(api_url='https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0/api/Region/A'):
            Fetches region data from the API and stores it in a dictionary.

        fetch_forecast_data():
            Fetches avalanche forecast data for each region for the next n_days_forecast days.

        get_region(region_id):
            Retrieves region information by ID.

        _create_forecast_layer_region(region_info):
            Creates a GeoJSON layer for a region's forecast data and saves it as a file.

        process_3003():
            Processes avalanche forecast data specifically for region '3003'.
    """

    def __init__(self, n_days_forecast=1, regions_list=None, serve_only=False):
        """
        Initializes the AvalancheForecastProcessing instance with the specified configuration.

        This method sets up the instance with the number of forecast days and a list of region IDs to process.
        It initializes a logger, prepares a dictionary to store region data, and sets up the export directory
        for saving processed GeoJSON files.

        Args:
            n_days_forecast (int): The number of days to forecast. Defaults to 1.
            regions_list (list, optional): A list of region IDs to process. If None, defaults to ['3003'].

        Attributes:
            logger (Logger): Logger instance for logging messages.
            regions_list (list): List of region IDs to process.
            regions (dict): Dictionary to store region data, including names and polygons.
            n_days_forecast (int): Number of days to forecast.
            maps_cache (MapsCaching): Instance of MapsCaching for managing map data.
            export_directory (str): Directory where processed GeoJSON files are saved.
        """
        self.logger = Logger.setup_logger('AvalancheForecastProcessing')
        if regions_list is None:
            #self.regions_list = ['3001', '3002', '3003', '3004']
            self.regions_list = ['3003']
        else:
            self.regions_list = [str(elem) for elem in regions_list]
        self.regions = {region_id: {} for region_id in self.regions_list}
        self.n_days_forecast = n_days_forecast
        self.maps_cache = MapsCaching()
        self.export_directory = './maps/avalanche_forecast'
        self.logger.info("AvalancheForecastProcessing initialized.")

        if os.environ.get('SWI_INSTANCE_SERVE_ONLY') == 'true' or serve_only:
            self.serve_only = True
            self.logger.info("This instance is in SERVE ONLY mode.")
        else:
            self.serve_only = False

    def _binary_to_directions(self, binary_string):
        """
        Converts a binary string to a list of cardinal and intercardinal directions.

        This method takes a binary string of length 8, where each bit represents a direction (N, NE, E, SE, S, SW, W, NW).
        It returns a list of directions corresponding to the positions where the binary string has a '1'.

        Args:
            binary_string (str): A binary string of length 8 representing directions.

        Returns:
            list: A list of directions (e.g., ['N', 'E', 'S']) based on the binary string.

        Raises:
            ValueError: If the binary string is not exactly 8 characters long.
        """
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

    def _create_geojson_from_dicts(self, gdf_dicts, colormap='viridis'):
        """
        Creates a GeoJSON FeatureCollection from a list of GeoDataFrame dictionaries, applying a colormap.

        This method takes a list of dictionaries, each containing a GeoDataFrame and associated metadata (label and description).
        It generates a GeoJSON FeatureCollection where each feature is styled with a color from the specified colormap.
        The geometries are transformed to the WGS 84 coordinate reference system (CRS) and aggregated into a MultiPolygon.

        Args:
            gdf_dicts (list): A list of dictionaries, each containing:
                - 'gdf' (GeoDataFrame): The GeoDataFrame containing geometries.
                - 'label' (str): The label for the feature.
                - 'description' (str): The description for the feature.
            colormap (str, optional): The name of the matplotlib colormap to use for coloring features. Defaults to 'viridis'.

        Returns:
            FeatureCollection or None: A GeoJSON FeatureCollection containing the styled features, or None if an error occurs.

        Raises:
            Exception: Logs any exceptions that occur during the creation of the GeoJSON, including a full traceback.
        """
        try:
            # Use the specified colormap from matplotlib
            cmap = plt.cm.get_cmap(colormap, len(gdf_dicts))

            # Define the target CRS (WGS 84)
            target_crs = CRS.from_epsg(4326)

            features = []
            for i, entry in enumerate(gdf_dicts):
                gdf = entry['gdf']
                label = entry['label']
                description = entry['description']

                # Get a color from the colormap
                color = cmap(i)

                # Aggregate all geometries into a list of Polygons
                polygons = []
                for _, row in gdf.iterrows():
                    geometry = row['geometry']
                    if isinstance(geometry, Polygon):
                        polygons.append(geometry)
                    elif isinstance(geometry, MultiPolygon):
                        polygons.extend(geometry.geoms)

                # Ensure that polygons is a list of valid polygons
                if polygons:
                    # Transform each polygon to the target CRS
                    transformer = Transformer.from_crs(gdf.crs, target_crs, always_xy=True)
                    transformed_polygons = [transform(transformer.transform, polygon) for polygon in polygons]

                    multipolygon = MultiPolygon(transformed_polygons)

                    feature = geojson.Feature(
                        geometry=mapping(multipolygon),
                        properties={
                            'name': label,
                            'description': description,
                            'color': f'#{int(color[0] * 255):02X}{int(color[1] * 255):02X}{int(color[2] * 255):02X}',
                            'fillOpacity' : 0.5

                        }
                    )
                    features.append(feature)

            feature_collection = geojson.FeatureCollection(features)
            return feature_collection
        except Exception as e:
            # Log the full traceback
            self.logger.error(f"Error creating GeoJSON: {e}\n{traceback.format_exc()}")
            return None

    def _save_geojson_to_file(self, geojson_obj, file_name):
        """
        Saves a GeoJSON object to a file in the export directory.

        This method ensures that the export directory exists and constructs the full file path for the GeoJSON file.
        It then saves the GeoJSON object to the specified file, logging success or any errors that occur during the process.

        Args:
            geojson_obj (dict): The GeoJSON object to save.
            file_name (str): The name of the file to save the GeoJSON object to, without the file extension.

        Raises:
            Exception: Logs any exceptions that occur during the saving process.
        """
        try:
            # Ensure the export directory exists
            os.makedirs(self.export_directory, exist_ok=True)

            # Construct the full file path
            file_path = os.path.join(self.export_directory, f"{str(file_name)}.geojson")

            # Save the GeoJSON object to the file
            with open(file_path, 'w') as file:
                json.dump(geojson_obj, file, indent=2)
            self.logger.info(f"GeoJSON saved successfully to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving GeoJSON to file: {e}")

    def clip_shapefile_with_gps_contour(self, gps_coordinates, shapefile_path):
        """
        Clips a shapefile using a contour defined by a list of GPS coordinates.

        This method creates a polygon from the provided GPS coordinates and uses it to clip features from a shapefile.
        It ensures that the polygon and shapefile are in the same coordinate reference system (CRS) before performing the clip operation.
        The method also checks for intersections and validity of the polygon, logging relevant information throughout the process.

        Parameters:
            gps_coordinates (list of tuples): List of tuples, where each tuple is (latitude, longitude) defining the contour.
            shapefile_path (str): Path to the shapefile to be clipped.

        Returns:
            GeoDataFrame: A GeoDataFrame containing the clipped features from the shapefile. If the polygon is invalid or
                          does not intersect with any features, an empty GeoDataFrame is returned.
        """
        """
        Clips a shapefile using a contour defined by a list of GPS coordinates.

        Parameters:
        - gps_coordinates: List of tuples, where each tuple is (latitude, longitude).
        - shapefile_path: Path to the shapefile.

        Returns:
        - GeoDataFrame containing the clipped features.
        """
        # Ensure the coordinates are in (latitude, longitude) format
        gps_coordinates = [(lat, lon) for lon, lat in gps_coordinates]

        # Create a polygon from the GPS coordinates
        polygon = Polygon(gps_coordinates)

        # Create a GeoDataFrame from the polygon with CRS WGS 84
        gdf_polygon = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[polygon])

        # Read the shapefile
        gdf = gpd.read_file(shapefile_path)

        # Log CRS information
        self.logger.info(f"Initial Shapefile CRS: {gdf.crs}")
        self.logger.info(f"Initial Polygon CRS: {gdf_polygon.crs}")

        # Reproject the polygon to match the CRS of the shapefile
        gdf_polygon = gdf_polygon.to_crs(gdf.crs)

        # Verify the CRS after reprojection
        self.logger.info(f"Polygon CRS after reprojection: {gdf_polygon.crs}")

        # Apply a small buffer to the polygon to account for precision issues
        gdf_polygon['geometry'] = gdf_polygon.buffer(10)  # Adjust the buffer size as needed

        # Check if the polygon is valid
        if not polygon.is_valid:
            self.logger.error("The polygon is not valid.")
            return gpd.GeoDataFrame()

        # Log bounds information
        self.logger.info(f"Shapefile bounds: {gdf.total_bounds}")
        self.logger.info(f"Polygon bounds: {gdf_polygon.total_bounds}")

        # Plot the shapefile and polygon for visual inspection
        #fig, ax = plt.subplots()
        #gdf.plot(ax=ax, color='blue', edgecolor='black')
        #gdf_polygon.plot(ax=ax, color='red', alpha=0.5)
        #plt.show()

        # Check if the polygon intersects with any feature in the shapefile
        intersects = gdf.intersects(gdf_polygon.union_all())
        if not intersects.any():
            self.logger.error("The polygon does not intersect with any features in the shapefile.")
            return gpd.GeoDataFrame()

        # Clip the shapefile using the polygon
        clipped_gdf = gdf.clip(gdf_polygon)

        # Check if the result is empty
        if clipped_gdf.empty:
            self.logger.warning("The clipped result is empty. Check if the polygon intersects with the shapefile.")

        return clipped_gdf


    def fetch_region_data(self, api_url='https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0/api/Region/A'):
        """
        Fetch region data from the API and store it in a dictionary.

        This method retrieves region data from a specified API URL and processes it to extract relevant information,
        such as the region ID, name, and polygon coordinates. The data is stored in a dictionary for further use.

        Args:
            api_url (str): The URL of the API to fetch region data. Defaults to the avalanche forecast API.

        Raises:
            requests.RequestException: If there is an error with the HTTP request, such as a network issue or invalid response.
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

        This method retrieves avalanche forecast data from an API for each region specified in the regions_list.
        It fetches data for a specified number of days starting from the current date. The forecast data includes
        avalanche problems, advice, validity periods, and danger levels. The method stores the most recent forecast
        for each day in a dictionary for further processing.

        Raises:
            requests.RequestException: If there is an error with the HTTP request, such as a network issue or invalid response.
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
                    #if forecast['IsTendency']:
                    #    continue  # Skip tendency forecasts

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
        Retrieve region information by ID.

        This method fetches and returns information for a specified region, including its name, polygon coordinates,
        and forecast data. It logs a message indicating whether the region information was successfully retrieved or not found.

        Args:
            region_id (str): The ID of the region to retrieve information for.

        Returns:
            dict or None: A dictionary containing the region's name, polygon, and forecast data if the region ID is found.
                           Returns None if the region ID is not found.
        """
        region_info = self.regions.get(region_id, None)
        if region_info:
            self.logger.info(f"Region {region_id} info retrieved.")
        else:
            self.logger.warning(f"Region {region_id} not found.")
        return region_info

    def _create_forecast_layer_region(self, region_info):
        """
        Creates a GeoJSON layer for a region's forecast data and saves it as a file.

        This method processes the forecast data for a specified region to generate a GeoJSON layer. It handles
        avalanche problems, orientations, and elevation ranges to create detailed GeoJSON features. The method
        saves the resulting GeoJSON to a file, including metadata such as the publish time and a link to the full forecast.

        Args:
            region_info (dict): A dictionary containing the region's name, polygon coordinates, and forecast data.

        Raises:
            Exception: Logs any exceptions that occur during the processing of the forecast data.
        """
        try:
            region_name = region_info['name']
            polygon = region_info['polygon']
            forecasts = region_info['forecast']

            self.logger.info(f"Region {region_name} info retrieved.")

            for date, forecast in forecasts.items():
                gdf_dict_list = []
                self.logger.info(f"Processing forecast for date: {forecast['ValidFrom']} & {date}")

                # Correct the condition to check 'MainText' in the current forecast
                if forecast.get('AvalancheProblems') is None or forecast.get('MainText') == "No Rating":
                    # Create an empty GeoJSON with available information
                    self.logger.info(f"No detailled AvalancheProblems for region {region_name} and date {date}")
                    geojson = {
                        "type": "FeatureCollection",
                        "features": [],
                    }
                else:

                    for problem in forecast['AvalancheProblems']:
                        if problem is None:
                            continue
                        label = problem['AvalancheProblemTypeName']
                        orientation_list = self._binary_to_directions(problem['ValidExpositions'])
                        description = f"{problem['TriggerSenitivityPropagationDestuctiveSizeText']} - ({problem['AvalCauseName']}) <br><i> {' '.join(orientation_list)}</i>"

                        self.logger.info(f"Orientation list for date = {date} - {orientation_list}")
                        e1, e2 = problem['ExposedHeight1'], problem['ExposedHeight2']
                        h_fill = problem['ExposedHeightFill']

                        if h_fill == 0:
                            e1, e2 = None, None
                        elif h_fill == 1:
                            e2 = None
                        elif h_fill == 2:
                            e1 = None

                        shape_path = self.maps_cache.get_steepness_contour(25, 65, orientations=orientation_list,
                                                                           elevation_start=e1, elevation_end=e2)

                        gdf_dict_list.append({
                            'gdf': self.clip_shapefile_with_gps_contour(polygon, shape_path),
                            'label': label,
                            'description': description,
                        })

                    self.logger.info(f"Len gdf_dict_list = {len(gdf_dict_list)}")
                    geojson = self._create_geojson_from_dicts(gdf_dict_list)
                geojson["date"] = forecast.get('PublishTime', None)
                geojson["lastDownload"] = datetime.now().isoformat()

                # Calculate the new date
                current_date = datetime.now()
                new_date = current_date + timedelta(
                    days=int(date))  # Assuming `date` is a string that can be converted to an integer
                formatted_date = new_date.strftime('%Y-%m-%d')

                # Encode the URL correctly
                base_url = "https://www.varsom.no/en/snow/forecast/warning/"
                region_encoded = urllib.parse.quote("Nordenskiöld Land")
                full_url = f"{base_url}{region_encoded}/{formatted_date}"

                geojson["description"] = (
                    f"<strong>Danger Level : {forecast.get('DangerLevelName', 'Unknown')}</strong> : "
                    f"{forecast.get('MainText', 'Unknown')} <br> "
                    f"<a target='_blank' rel='noopener noreferrer' href='{full_url}'>Full forecast on Varsom.no</a>"
                )

                self._save_geojson_to_file(geojson, date)

        except Exception as e:
            self.logger.error(f"Error processing forecast: {e}")

    def process_3003(self):
        """
        Processes avalanche forecast data specifically for region '3003' (Nordenskiöld Land).

        This method orchestrates the fetching of region data and forecast data for region '3003',
        and then creates a GeoJSON layer for the region's forecast. It combines the functionalities
        of fetching data, processing it, and generating visual representations of avalanche risks.

        The method performs the following steps:
        1. Fetches region data for region '3003'.
        2. Fetches avalanche forecast data for the specified number of days.
        3. Creates a GeoJSON layer for the region's forecast data and saves it as a file.

        Raises:
            Exception: Logs any exceptions that occur during the processing of the forecast data.
        """
        if self.serve_only:
            return -1
        self.fetch_region_data()
        self.fetch_forecast_data()
        self._create_forecast_layer_region(self.get_region('3003'))
