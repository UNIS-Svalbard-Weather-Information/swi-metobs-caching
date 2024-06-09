import netCDF4 as nc
import json
import numpy as np
import os
import sys
from datetime import date, datetime, timedelta

# Directory to store data files; should end with a slash
data_directory = "./data/"
# Add import functions path to system path
sys.path.append(os.path.join(os.path.dirname(__file__), './import_functions'))

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.

    Parameters:
    lat1 (float): Latitude of the first point.
    lon1 (float): Longitude of the first point.
    lat2 (float): Latitude of the second point.
    lon2 (float): Longitude of the second point.

    Returns:
    float: Distance between the two points in meters.
    """
    R = 6371000  # radius of Earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def get_url(url, date):
    """
    Format a URL with a given date.

    Parameters:
    url (str): The base URL with placeholders for date formatting.
    date (datetime.date): The date to format into the URL.

    Returns:
    str: The formatted URL.
    """
    return date.strftime(url)

def netcdf_boat(url, variables, duration, station_id):
    """
    Process a NetCDF file to extract boat data over a specified duration.

    Parameters:
    url (str): The base URL for the NetCDF file.
    variables (dict): A dictionary mapping variable names to NetCDF variable names.
    duration (int): Duration in hours for which data is to be fetched.
    station_id (str): Identifier for the station.

    Returns:
    dict: Processed data including latest location, wind information, and track history.
    """
    try:
        try:
            # Attempt to load the dataset for today
            dataset = nc.Dataset(get_url(url, date.today()))
        except:
            # Fallback to the previous day if today's data is not available
            dataset = nc.Dataset(get_url(url, date.today() - timedelta(1)))
        
        times = dataset.variables['time'][:]
        current_time = times[-1]
        time_frame = current_time - duration * 3600
        mask = times >= time_frame

        file_path = data_directory + station_id + "_" + str(duration) + "_" + str(current_time) + ".json"

        if os.path.exists(file_path):
            # If the data file already exists, load and return it
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            data_points = []
            last_point = None
            #for i in range(len(times)):
            for i in range(len(times) - 1, -1, -1): #follow the list backward. So the distance calculation will keep the more recent data.
                try:
                    if not mask[i]:
                        continue

                    data_point = {
                        'time': float(times[i]),
                        'lat': float(dataset.variables['latitude'][i]),
                        'lon': float(dataset.variables['longitude'][i]),
                        'airTemperature': float(dataset.variables[variables.get('airTemperature')][i]) if variables.get('airTemperature') else None,
                        'seaSurfaceTemperature': float(dataset.variables[variables.get('seaSurfaceTemperature')][i]) if variables.get('seaSurfaceTemperature') else None,
                        'windSpeed': float(dataset.variables[variables.get('windSpeed')][i]) if variables.get('windSpeed') else None,
                        'windDirection': float(dataset.variables[variables.get('windDirection')][i]) if variables.get('windDirection') else None,
                        'relativeHumidity': float(dataset.variables[variables.get('relativeHumidity')][i]) if variables.get('relativeHumidity') else None,
                    }

                    # Replace NaN values with None
                    for key, value in data_point.items():
                        if isinstance(value, float) and np.isnan(value):
                            data_point[key] = None

                    # Include point if it's the first one, or if it's 100m away from the last point
                    if last_point is None or haversine(last_point['lat'], last_point['lon'], data_point['lat'], data_point['lon']) >= 100:
                        data_points.append(data_point)
                        last_point = data_point
                except:
                    pass

            latest_data = data_points[0]
            track = [{'lat': dp['lat'], 'lon': dp['lon'], 'variable': dp} for dp in data_points]

            data_ready =  {
                'lat': latest_data['lat'],
                'lon': latest_data['lon'],
                'windSpeed': latest_data['windSpeed'],
                'windDirection': latest_data['windDirection'],
                'track': track,
                'latest': latest_data  # Add latest data for the popup
            }

            # Save the processed data to a file
            with open(file_path, 'w') as f:
                json.dump(data_ready, f)
            
            return data_ready
    except Exception as e:
        print(f"Error processing NetCDF file: {e}")
        return {}
