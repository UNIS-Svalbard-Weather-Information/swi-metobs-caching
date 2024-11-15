import os
import requests
import geopandas as gpd

def create_ice_chart_geojson(output_dir="./maps/ice_chart_data"):
    """
    Downloads the ice chart shapefiles from MET Norway, processes them,
    and generates a GeoJSON file.

    Parameters:
        output_dir (str): Directory where files will be saved and the GeoJSON generated.
    Returns:
        str: Path to the generated GeoJSON file.
    """
    # File URLs for the ice chart
    urls = {
        "shp": "https://cryo.met.no/sites/cryo.met.no/files/latest/chart_ice.shp",
        "shx": "https://cryo.met.no/sites/cryo.met.no/files/latest/chart_ice.shx",
        "dbf": "https://cryo.met.no/sites/cryo.met.no/files/latest/chart_ice.dbf",
        "prj": "https://cryo.met.no/sites/cryo.met.no/files/latest/chart_ice.prj",
    }

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Download the files
    print("Downloading files...")
    for ext, url in urls.items():
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(output_dir, f"chart_ice.{ext}")
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded {url}")
        else:
            print(f"Failed to download {url}. Status code: {response.status_code}")

    # Check if all required files are downloaded
    required_files = [f"chart_ice.{ext}" for ext in urls.keys()]
    missing_files = [file for file in required_files if not os.path.exists(os.path.join(output_dir, file))]
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {missing_files}")

    # Load the shapefile using GeoPandas
    print("Loading shapefile...")
    shapefile_path = os.path.join(output_dir, "chart_ice.shp")
    gdf = gpd.read_file(shapefile_path)

    # Define color mapping (adjust based on your data attribute)
    color_map = {
        "Open Water": "#0000FF",
        "Very Light Ice": "#00FFFF",
        "Light Ice": "#00FF00",
        "Moderate Ice": "#FFFF00",
        "Heavy Ice": "#FF0000",
        "Very Heavy Ice": "#800080",
    }

    # Add a 'color' property based on the ice category
    if 'ice_category' in gdf.columns:
        gdf['color'] = gdf['ice_category'].map(color_map).fillna("#808080")  # Default to gray
    else:
        print("Warning: 'ice_category' attribute not found. Adding default color.")
        gdf['color'] = "#808080"

    # Export to GeoJSON
    geojson_path = os.path.join(output_dir, "chart_ice.geojson")
    print(f"Saving GeoJSON to {geojson_path}...")
    gdf.to_file(geojson_path, driver="GeoJSON")

    print(f"GeoJSON file created at: {geojson_path}")
    return geojson_path

# Example usage
if __name__ == "__main__":
    geojson_path = create_ice_chart_geojson()
    print(f"Generated GeoJSON is available at: {geojson_path}")
