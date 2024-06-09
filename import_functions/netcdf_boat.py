import netCDF4 as nc
import json
import numpy as np
import json
import os
import sys
from datetime import date, datetime, timedelta

data_directory = "./data/" #shoudl end with /
sys.path.append(os.path.join(os.path.dirname(__file__), './import_functions'))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def get_url(url, date):
    return date.strftime(url)



def netcdf_boat(url, variables, duration, station_id):
    try:
        try:
            dataset = nc.Dataset(get_url(url, date.today()))
        except:
            dataset = nc.Dataset(get_url(url, date.today()- timedelta(1)))
        
        times = dataset.variables['time'][:]
        current_time = times[-1]
        time_frame = current_time - duration * 3600
        mask = times >= time_frame

        file_path = data_directory + station_id + "_" + str(duration) + "_" + str(current_time) + ".json"

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
            
        else:
            data_points = []
            last_point = None
            for i in range(len(times)):
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

                    # Replace NaN with None
                    for key, value in data_point.items():
                        if isinstance(value, float) and np.isnan(value):
                            data_point[key] = None


                    # Filter points: Include point if it's the first one, or if it's 100m away from the last point
                    if last_point is None or haversine(last_point['lat'], last_point['lon'], data_point['lat'], data_point['lon']) >= 100:
                        data_points.append(data_point)
                        last_point = data_point
                except:
                    pass

            latest_data = data_points[-1]
            track = [{'lat': dp['lat'], 'lon': dp['lon'], 'variable': dp} for dp in data_points]
            print(track)

            data_ready =  {
                'lat': latest_data['lat'],
                'lon': latest_data['lon'],
                'windSpeed': latest_data['windSpeed'],
                'windDirection': latest_data['windDirection'],
                'track': track,
                'latest': latest_data  # Add latest data for the popup
            }

            with open(file_path, 'w') as f:
                json.dump(data_ready, f)
            
            return data_ready
            
    except Exception as e:
        print(f"Error processing NetCDF file: {e}")
        return {}



# def process_netcdf_file(filepath, variables, duration):
#     try:
#         dataset = nc.Dataset(filepath)
#         times = dataset.variables['time'][:]
#         current_time = times[-1]
#         time_frame = current_time - duration * 3600

#         mask = times >= time_frame

#         data_points = []
#         last_point = None
#         for i in range(len(times)):
#             if not mask[i]:
#                 continue

#             data_point = {
#                 'time': float(times[i]),
#                 'lat': float(dataset.variables['latitude'][i]),
#                 'lon': float(dataset.variables['longitude'][i]),
#                 'airTemperature': float(dataset.variables[variables.get('airTemperature')][i]) if variables.get('airTemperature') else None,
#                 'seaSurfaceTemperature': float(dataset.variables[variables.get('seaSurfaceTemperature')][i]) if variables.get('seaSurfaceTemperature') else None,
#                 'windSpeed': float(dataset.variables[variables.get('windSpeed')][i]) if variables.get('windSpeed') else None,
#                 'windDirection': float(dataset.variables[variables.get('windDirection')][i]) if variables.get('windDirection') else None,
#                 'relativeHumidity': float(dataset.variables[variables.get('relativeHumidity')][i]) if variables.get('relativeHumidity') else None,
#             }

#             # Replace NaN with None
#             for key, value in data_point.items():
#                 if isinstance(value, float) and np.isnan(value):
#                     data_point[key] = None

#             # Filter points: Include point if it's the first one, or if it's 100m away from the last point
#             if last_point is None or haversine(last_point['lat'], last_point['lon'], data_point['lat'], data_point['lon']) >= 100:
#                 data_points.append(data_point)
#                 last_point = data_point

#         latest_data = data_points[-1]
#         track = [{'lat': dp['lat'], 'lon': dp['lon'], 'variable': dp} for dp in data_points]

#         return {
#             'lat': latest_data['lat'],
#             'lon': latest_data['lon'],
#             'windSpeed': latest_data['windSpeed'],
#             'windDirection': latest_data['windDirection'],
#             'track': track,
#             'latest': latest_data  # Add latest data for the popup
#         }
#     except Exception as e:
#         print(f"Error processing NetCDF file: {e}")
#         return {}