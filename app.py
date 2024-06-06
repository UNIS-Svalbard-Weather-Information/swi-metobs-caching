from flask import Flask, jsonify, render_template, request
import netCDF4 as nc
import json
import numpy as np

app = Flask(__name__)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def process_netcdf_file(filepath, variables, duration):
    try:
        dataset = nc.Dataset(filepath)
        times = dataset.variables['time'][:]
        current_time = times[-1]
        time_frame = current_time - duration * 3600

        mask = times >= time_frame

        data_points = []
        last_point = None
        for i in range(len(times)):
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
            if last_point is None or haversine(last_point['lat'], last_point['lon'], data_point['lat'], data_point['lon']) >= 200:
                data_points.append(data_point)
                last_point = data_point

        latest_data = data_points[-1]
        track = [{'lat': dp['lat'], 'lon': dp['lon'], 'variable': dp} for dp in data_points]
        print(len(track))
        return {
            'lat': latest_data['lat'],
            'lon': latest_data['lon'],
            'windSpeed': latest_data['windSpeed'],
            'windDirection': latest_data['windDirection'],
            'track': track
        }
    except Exception as e:
        print(f"Error processing NetCDF file: {e}")
        return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mobile-station-data/<station_id>')
def get_mobile_station_data(station_id):
    try:
        duration = int(request.args.get('duration', 1))
        with open('static/config/mobile_stations.json') as f:
            stations = json.load(f)
            station = next((s for s in stations if s['id'] == station_id), None)
            if not station:
                return jsonify({'error': 'Station not found'}), 404

        data = process_netcdf_file(station['netcdf_file'], station['variables'], duration)
        return jsonify(data)
    except Exception as e:
        print(f"Error retrieving station data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
