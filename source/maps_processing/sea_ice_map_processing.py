import sys
import os
from time import strftime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import requests
import zipfile
import geopandas as gpd
import json
from shapely.geometry import mapping, box
from datetime import datetime, timedelta
import re
import tempfile

from source.logger.logger import Logger


class SeaIceCache:
    """
    A class to manage and generate sea ice chart GeoJSON data from the Cryo.met.no data.

    This class provides functionality to download sea ice chart data, process it to clip and mask land areas,
    and generate GeoJSON files representing sea ice conditions. It uses a local shapefile to mask land areas
    and focuses on the Svalbard region by default. The class ensures that the output GeoJSON file is up-to-date
    and logs the operations performed.

    Attributes:
        output_dir (str): The directory where the output GeoJSON file will be saved.
        shapefile_path (str): The local file path to the shapefile used for masking land areas.
        logger (Logger): Logger instance for logging messages.

    Methods:
        __init__(output_dir="./maps/", shapefile_path="static/maps/S1000_Land_f"):
            Initializes the SeaIceCache instance with the specified output directory and shapefile path.

        clip_and_mask_water_area(gdf, svalbard_bbox=(7.5, 74.0, 36.0, 81.0)):
            Clips the input GeoDataFrame to a specified bounding box and masks out land areas using a local shapefile.

        is_recent_file(filepath, max_age_minutes=30):
            Checks if the specified file exists and is recent based on its last modification time.

        create_ice_chart_geojson(output_geojson="ice_chart.geojson", url="https://cryo.met.no/sites/cryo/files/latest/NIS_arctic_latest_pl_a.zip", force=False):
            Downloads and processes sea ice chart data to generate a GeoJSON file, clipping and masking as necessary.
    """
    def __init__(self, output_dir="./maps/", shapefile_path="static/maps/S1000_Land_f"):
        """
        Initialize a SeaIceCache instance to manage and generate sea ice chart GeoJSON data.

        This instance is configured with an output directory for the generated GeoJSON file and a path to a local shapefile
        that is used to mask land areas from the sea ice data. A logger is set up to record the operations.

        Args:
            output_dir (str): The directory where the output GeoJSON file will be saved.
                Default is "./maps/".
            shapefile_path (str): The local file path to the shapefile used for masking land areas.
                Default is "static/maps/S1000_Land_f".

        Returns:
            None
        """
        self.output_dir = output_dir
        self.shapefile_path = shapefile_path
        self.logger = Logger.setup_logger('Sea Ice Caching')
        os.makedirs(self.output_dir, exist_ok=True)

    def clip_and_mask_water_area(self, gdf, svalbard_bbox=(7.5, 74.0, 36.0, 81.0)):
        """
        Clip the input GeoDataFrame to a specified bounding box and mask out land areas using a local shapefile.

        This method takes an input GeoDataFrame containing sea ice data and performs two operations:
        1. It clips the GeoDataFrame to the Svalbard bounding box defined by the provided coordinates.
        2. It reads a local shapefile (representing land areas), transforms it to the same coordinate reference system (CRS)
           as the input GeoDataFrame, and overlays it with the clipped data to remove land areas, leaving only water areas.

        Args:
            gdf (GeoDataFrame): The input GeoDataFrame containing sea ice geometries.
            svalbard_bbox (tuple, optional): A tuple of four floats (minx, miny, maxx, maxy) representing the bounding box for Svalbard.
                Default is (7.5, 74.0, 36.0, 81.0).

        Returns:
            GeoDataFrame: A GeoDataFrame containing only the water areas within the specified bounding box after masking out land.
        """
        self.logger.info("Starting clip and mask process...")
        svalbard_geom = box(*svalbard_bbox)
        svalbard_gdf = gpd.GeoDataFrame([1], geometry=[svalbard_geom], crs=gdf.crs)
        gdf_clipped = gpd.clip(gdf, svalbard_gdf)

        self.logger.info("GeoDataFrame clipped to Svalbard bounding box.")
        land_gdf = gpd.read_file(self.shapefile_path).to_crs(gdf.crs)
        gdf_water_only = gpd.overlay(gdf_clipped, land_gdf, how="difference")

        self.logger.info("Land areas successfully masked out.")
        return gdf_water_only

    def is_recent_file(self, filepath, max_age_minutes=30):
        """
        Check if the specified file exists and is recent based on its last modification time.

        This method determines whether a file exists at the given filepath and verifies that its modification time
        is within the allowed maximum age in minutes.

        Args:
            filepath (str): The path to the file to check.
            max_age_minutes (int, optional): The maximum allowed age of the file in minutes.
                Default is 30.

        Returns:
            bool: True if the file exists and its modification time is within the specified max_age_minutes; False otherwise.
        """
        if not os.path.exists(filepath):
            return False
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        return datetime.now() - file_mod_time <= timedelta(minutes=max_age_minutes)

    def create_ice_chart_geojson(self, output_geojson="ice_chart.geojson",
                                 url="https://cryo.met.no/sites/cryo/files/latest/NIS_arctic_latest_pl_a.zip",
                                 force=False):
        """
        Download and process sea ice chart data to generate a GeoJSON file.

        This method downloads a ZIP archive containing sea ice chart shapefiles from the specified URL, extracts the shapefile,
        and processes the data by:

          - Clipping the data to the Svalbard region.
          - Masking out land areas using the local shapefile.
          - Dissolving geometries by ice classification and assigning predefined colors.
          - Excluding features labeled as "Ice Free".

        The method then creates a GeoJSON file that includes the processed features along with metadata such as the data date
        (extracted from the shapefile filename) and the timestamp of the download.

        Args:
            output_geojson (str, optional): The filename for the output GeoJSON file.
                Default is "ice_chart.geojson".
            url (str, optional): The URL from which to download the sea ice chart data ZIP archive.
                Default is "https://cryo.met.no/sites/cryo/files/latest/NIS_arctic_latest_pl_a.zip".
            force (bool, optional): If True, forces re-download and processing even if a recent GeoJSON file already exists.
                Default is False.

        Returns:
            str: The full file path to the generated GeoJSON file.

        Raises:
            Exception: If the download fails (i.e., the HTTP response status code is not 200).
            FileNotFoundError: If no shapefile is found in the downloaded ZIP archive.
        """
        geojson_path = os.path.join(self.output_dir, output_geojson)
        if not force and self.is_recent_file(geojson_path, max_age_minutes=30):
            self.logger.info(f"GeoJSON file {geojson_path} is recent. Skipping processing.")
            return geojson_path

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file_path = os.path.join(temp_dir, "NIS_arctic_latest.zip")
            self.logger.info(f"Downloading data from {url}...")
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                with open(zip_file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)
                self.logger.info("Download complete.")
            else:
                self.logger.error(f"Failed to download file: {response.status_code}")
                raise Exception(f"Download failed: {response.status_code}")

            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            shapefiles = [f for f in os.listdir(temp_dir) if f.endswith(".shp")]
            if not shapefiles:
                raise FileNotFoundError("No shapefile found in the downloaded ZIP.")

            shapefile_path = os.path.join(temp_dir, shapefiles[0])
            gdf = gpd.read_file(shapefile_path)
            gdf = self.clip_and_mask_water_area(gdf)

            class_colors = {
                "Fast Ice": "#808080", "Very Close Drift Ice": "#FF0000", "Close Drift Ice": "#FFA500",
                "Open Drift Ice": "#FFFF00", "Very Open Drift Ice": "#90EE90", "Open Water": "#ADD8E6"
            }
            if "Ice Free" in gdf["NIS_CLASS"].unique():
                gdf = gdf[gdf["NIS_CLASS"] != "Ice Free"]

            features = []
            for nis_class, color in class_colors.items():
                if nis_class in gdf["NIS_CLASS"].unique():
                    class_gdf = gdf[gdf["NIS_CLASS"] == nis_class]
                    dissolved = class_gdf.dissolve(by="NIS_CLASS").geometry.iloc[0]
                    features.append({
                        "type": "Feature",
                        "properties": {"name": nis_class, "color": color},
                        "geometry": mapping(dissolved),
                    })

            # Extract date from filename
            match = re.search(r"NIS_arctic_(\d{8})_pl_a\.shp", shapefile_path)
            if match:
                date_str = match.group(1)
                date_obj = datetime.strptime(date_str, "%Y%m%d")

            geojson_data = {
                "type": "FeatureCollection",
                "features": features,
                "date": date_obj.isoformat(),
                "lastDownload": datetime.now().isoformat()
            }

            with open(geojson_path, "w") as f:
                json.dump(geojson_data, f)
            self.logger.info(f"GeoJSON file created: {geojson_path}")

        return geojson_path


if __name__ == "__main__":
    sea_ice_cache = SeaIceCache()
    try:
        geojson_path = sea_ice_cache.create_ice_chart_geojson(force=True)
        print(f"Generated GeoJSON is available at: {geojson_path}")
    except Exception as e:
        sea_ice_cache.logger.error(f"An error occurred: {e}")