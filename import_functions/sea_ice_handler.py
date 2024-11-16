import os
import requests
import zipfile
import geopandas as gpd
import logging
import json
from shapely.geometry import mapping, box



def clip_and_mask_water_area(gdf, shapefile_path="static/maps/S1000_Land_f", svalbard_bbox=(7.5, 74.0, 36.0, 81.0)):
    """
    Clips the input GeoDataFrame to the Svalbard bounding box and masks out the land areas using a local shapefile.

    To increase the resolution of the processing of the contour line, you can replace S1000_Land_f by S100_Land_f

    Parameters:
        gdf (GeoDataFrame): The GeoDataFrame to process.
        shapefile_path (str): Path to the shapefile containing land contours.
        svalbard_bbox (tuple): The bounding box for Svalbard (minx, miny, maxx, maxy).

    Returns:
        GeoDataFrame: The clipped and water-masked GeoDataFrame.
    """
    logging.info("Starting clip and mask process...")

    # Step 1: Clip GeoDataFrame to the bounding box of Svalbard
    svalbard_geom = box(*svalbard_bbox)  # Create a box geometry using the bounding box
    svalbard_gdf = gpd.GeoDataFrame([1], geometry=[svalbard_geom], crs=gdf.crs)
    gdf_clipped = gpd.clip(gdf, svalbard_gdf)  # Clip the data to the bounding box
    logging.info("GeoDataFrame clipped to Svalbard bounding box.")

    # Step 2: Load the land contour shapefile
    logging.info(f"Loading land contour shapefile from {shapefile_path}...")
    land_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS of the land contour matches the GeoDataFrame
    land_gdf = land_gdf.to_crs(gdf.crs)
    logging.info("Land contour CRS matched to GeoDataFrame CRS.")

    # Step 3: Mask out the land areas by performing a difference operation
    gdf_water_only = gpd.overlay(gdf_clipped, land_gdf, how="difference")
    logging.info("Land areas successfully masked out.")

    return gdf_water_only


def create_ice_chart_geojson(output_dir="./maps/ice_chart_data",
                             output_geojson="ice_chart.geojson",
                             url="https://cryo.met.no/sites/cryo/files/latest/NIS_arctic_latest_pl_a.zip"):
    """
    Downloads the latest zipped shapefile from MET Norway, processes it,
    and generates a single GeoJSON file with all features grouped by the NIS_CLASS field.

    Parameters:
        output_dir (str): Directory where files will be saved and the GeoJSON generated.
        output_geojson (str): Name of the output GeoJSON file.
        url (str): URL of the zipped shapefile to download.
    Returns:
        str: Path to the generated GeoJSON file.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Download the zip file
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

    # Extract the zip file
    logger.info("Extracting downloaded files...")
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(output_dir)

    # Find the shapefile (.shp) in the extracted files
    shapefiles = [f for f in os.listdir(output_dir) if f.endswith(".shp")]
    if not shapefiles:
        logger.error("No shapefile found in the downloaded ZIP.")
        raise FileNotFoundError("No shapefile found in the downloaded ZIP.")
    shapefile_path = os.path.join(output_dir, shapefiles[0])

    # Load the shapefile using GeoPandas
    logger.info(f"Loading shapefile {shapefile_path}...")
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        logger.error(f"Failed to load the shapefile: {e}")
        raise

    # Clip and mask the GeoDataFrame
    try:
        gdf = clip_and_mask_water_area(gdf)
        logger.info("GeoDataFrame successfully clipped and masked.")
    except Exception as e:
        logger.error(f"Failed to clip and mask: {e}")
        raise

    # Fixed colors from the legend
    class_colors = {
        "Fast Ice": "#808080",  # Gray
        "Very Close Drift Ice": "#FF0000",  # Red
        "Close Drift Ice": "#FFA500",  # Orange
        "Open Drift Ice": "#FFFF00",  # Yellow
        "Very Open Drift Ice": "#90EE90",  # Light Green
        "Open Water": "#ADD8E6",  # Light Blue
    }

    # Filter out the 'Ice Free' field if present
    if "Ice Free" in gdf["NIS_CLASS"].unique():
        gdf = gdf[gdf["NIS_CLASS"] != "Ice Free"]

    # Generate features for GeoJSON using fixed colors
    features = []
    for nis_class in class_colors.keys():
        if nis_class in gdf["NIS_CLASS"].unique():
            class_gdf = gdf[gdf["NIS_CLASS"] == nis_class]
            dissolved = class_gdf.dissolve(by="NIS_CLASS").geometry.iloc[0]

            feature = {
                "type": "Feature",
                "properties": {
                    "name": nis_class,
                    "color": class_colors[nis_class],
                },
                "geometry": mapping(dissolved),
            }
            features.append(feature)
    # Create the GeoJSON structure
    geojson_data = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Save to a GeoJSON file
    geojson_path = os.path.join(output_dir, output_geojson)
    with open(geojson_path, "w") as f:
        json.dump(geojson_data, f)
    logger.info(f"GeoJSON file created: {geojson_path}")

    return geojson_path


# Example usage
if __name__ == "__main__":
    try:
        geojson_path = create_ice_chart_geojson()
        print(f"Generated GeoJSON is available at: {geojson_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
