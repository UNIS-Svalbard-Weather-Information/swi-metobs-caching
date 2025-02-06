import sys
import os


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
    def __init__(self, output_dir="./maps/", shapefile_path="static/maps/S1000_Land_f"):
        self.output_dir = output_dir
        self.shapefile_path = shapefile_path
        self.logger = Logger.setup_logger('Sea Ice Caching')
        os.makedirs(self.output_dir, exist_ok=True)

    def clip_and_mask_water_area(self, gdf, svalbard_bbox=(7.5, 74.0, 36.0, 81.0)):
        """
        Clips the input GeoDataFrame to the Svalbard bounding box and masks out the land areas using a local shapefile.
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
        """Checks if the file exists and is recent."""
        if not os.path.exists(filepath):
            return False
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        return datetime.now() - file_mod_time <= timedelta(minutes=max_age_minutes)

    def create_ice_chart_geojson(self, output_geojson="ice_chart.geojson",
                                 url="https://cryo.met.no/sites/cryo/files/latest/NIS_arctic_latest_pl_a.zip",
                                 force=False):
        """Downloads and processes ice chart data, generating a GeoJSON file."""
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

            geojson_data = {
                "type": "FeatureCollection",
                "features": features,
                "date": datetime.now().isoformat(),
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