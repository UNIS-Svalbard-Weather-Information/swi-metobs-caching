import os
import requests
import zipfile
import geopandas as gpd
import logging
import json
from shapely.geometry import mapping, box
from datetime import datetime, timedelta
import re


def clip_and_mask_water_area(gdf, shapefile_path="static/maps/S1000_Land_f", svalbard_bbox=(7.5, 74.0, 36.0, 81.0)):
    """
    Clips the input GeoDataFrame to the Svalbard bounding box and masks out the land areas using a local shapefile.

    Parameters:
        gdf (GeoDataFrame): The GeoDataFrame to process.
        shapefile_path (str): Path to the shapefile containing land contours.
        svalbard_bbox (tuple): The bounding box for Svalbard (minx, miny, maxx, maxy).

    Returns:
        GeoDataFrame: The clipped and water-masked GeoDataFrame.
    """
    logging.info("Starting clip and mask process...")

    svalbard_geom = box(*svalbard_bbox)  # Create a box geometry using the bounding box
    svalbard_gdf = gpd.GeoDataFrame([1], geometry=[svalbard_geom], crs=gdf.crs)
    gdf_clipped = gpd.clip(gdf, svalbard_gdf)  # Clip the data to the bounding box
    logging.info("GeoDataFrame clipped to Svalbard bounding box.")

    logging.info(f"Loading land contour shapefile from {shapefile_path}...")
    land_gdf = gpd.read_file(shapefile_path)
    land_gdf = land_gdf.to_crs(gdf.crs)  # Ensure CRS matches
    logging.info("Land contour CRS matched to GeoDataFrame CRS.")

    gdf_water_only = gpd.overlay(gdf_clipped, land_gdf, how="difference")
    logging.info("Land areas successfully masked out.")

    return gdf_water_only


def is_recent_file(filepath, max_age_minutes=30):
    """
    Checks if the file exists and was modified within the specified time frame.

    Parameters:
        filepath (str): Path to the file to check.
        max_age_minutes (int): Maximum allowed file age in minutes.

    Returns:
        bool: True if the file is recent, False otherwise.
    """
    if not os.path.exists(filepath):
        return False

    file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
    return datetime.now() - file_mod_time <= timedelta(minutes=max_age_minutes)


def create_ice_chart_geojson(output_dir="./maps/ice_chart_data",
                             output_geojson="ice_chart.geojson",
                             url="https://cryo.met.no/sites/cryo/files/latest/NIS_arctic_latest_pl_a.zip",
                             force=False):
    """
    Downloads and processes ice chart data, generating a GeoJSON file.

    Parameters:
        output_dir (str): Directory where files will be saved and the GeoJSON generated.
        output_geojson (str): Name of the output GeoJSON file.
        url (str): URL of the zipped shapefile to download.
        force (bool): Force redownload and reprocess data even if GeoJSON exists and is recent.

    Returns:
        str: Path to the generated GeoJSON file.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    os.makedirs(output_dir, exist_ok=True)

    geojson_path = os.path.join(output_dir, output_geojson)

    # Check if the GeoJSON file exists and is recent
    if not force and is_recent_file(geojson_path, max_age_minutes=30):
        logger.info(f"GeoJSON file {geojson_path} is recent. Skipping processing.")
        return geojson_path

    zip_file_path = os.path.join(output_dir, "NIS_arctic_latest.zip")
    logger.info(f"Downloading data from {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(zip_file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        logger.info(f"Downloaded and saved to {zip_file_path}")
    else:
        logger.error(f"Failed to download the file. Status code: {response.status_code}")
        raise Exception(f"Failed to download the file. Status code: {response.status_code}")

    logger.info("Extracting downloaded files...")
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(output_dir)

    shapefiles = [f for f in os.listdir(output_dir) if f.endswith(".shp")]

    # Regular expression to extract YYYYMMDD
    match = re.search(r'\d{8}', shapefiles[0])
    if match:
        date_str = match.group()  # '20241115'
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        logger.info(f"Shape file from {date_obj}")  # Output: 2024-11-15 00:00:00
    else:
        date_obj = datetime.strptime("19000101", '%Y%m%d')
        logger.info(f"No date found in the shape file")

    if not shapefiles:
        logger.error("No shapefile found in the downloaded ZIP.")
        raise FileNotFoundError("No shapefile found in the downloaded ZIP.")
    shapefile_path = os.path.join(output_dir, shapefiles[0])

    logger.info(f"Loading shapefile {shapefile_path}...")
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        logger.error(f"Failed to load the shapefile: {e}")
        raise

    try:
        gdf = clip_and_mask_water_area(gdf)
        logger.info("GeoDataFrame successfully clipped and masked.")
    except Exception as e:
        logger.error(f"Failed to clip and mask: {e}")
        raise

    class_colors = {
        "Fast Ice": "#808080", "Very Close Drift Ice": "#FF0000", "Close Drift Ice": "#FFA500",
        "Open Drift Ice": "#FFFF00", "Very Open Drift Ice": "#90EE90", "Open Water": "#ADD8E6"
    }

    if "Ice Free" in gdf["NIS_CLASS"].unique():
        gdf = gdf[gdf["NIS_CLASS"] != "Ice Free"]

    features = []
    for nis_class in class_colors.keys():
        if nis_class in gdf["NIS_CLASS"].unique():
            class_gdf = gdf[gdf["NIS_CLASS"] == nis_class]
            dissolved = class_gdf.dissolve(by="NIS_CLASS").geometry.iloc[0]
            feature = {
                "type": "Feature",
                "properties": {"name": nis_class, "color": class_colors[nis_class]},
                "geometry": mapping(dissolved),
            }
            features.append(feature)

    geojson_data = {"type": "FeatureCollection", "features": features, "date" : date_obj.isoformat(), "lastDownload" : datetime.now().isoformat()}


    with open(geojson_path, "w") as f:
        json.dump(geojson_data, f)
    logger.info(f"GeoJSON file created: {geojson_path}")

    return geojson_path


if __name__ == "__main__":
    try:
        geojson_path = create_ice_chart_geojson(force=True)
        print(f"Generated GeoJSON is available at: {geojson_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
