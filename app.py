from flask import Flask, jsonify, render_template, request
import netCDF4 as nc
import numpy as np
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

def process_netcdf_file(filepath, duration, variable_name):
    dataset = nc.Dataset(filepath)
    times = dataset.variables['time'][:]
    lats = dataset.variables['latitude'][:]
    lons = dataset.variables['longitude'][:]
    variable_data = dataset.variables[variable_name][:] if variable_name else None

    # Convert netCDF times to datetime objects
    base_time = datetime(1970, 1, 1)
    times = np.array([base_time + timedelta(seconds=float(t)) for t in times])

    # Filter data based on the duration
    end_time = times[-1]
    start_time = end_time - timedelta(hours=duration)
    mask = (times >= start_time) & (times <= end_time)

    data_points = []
    for i in range(len(times)):
        if mask[i]:
            point = {
                'time': times[i].isoformat(),
                'lat': float(lats[i]),
                'lon': float(lons[i]),
                'windSpeed': float(dataset.variables['wind_speed_corrected'][i]),
                'windDirection': float(dataset.variables['wind_direction_corrected'][i])
            }
            if variable_data is not None:
                point['variable'] = float(variable_data[i])
            data_points.append(point)

    if data_points:
        latest_data = data_points[-1]
    else:
        latest_data = {
            'lat': 0, 'lon': 0, 'windSpeed': 0, 'windDirection': 0,
            'variable': 0 if variable_data is not None else None
        }

    track = [{'lat': dp['lat'], 'lon': dp['lon'], 'variable': dp.get('variable', None)} for dp in data_points]

    return {
        'lat': latest_data['lat'],
        'lon': latest_data['lon'],
        'windSpeed': latest_data['windSpeed'],
        'windDirection': latest_data['windDirection'],
        'variable': latest_data.get('variable', None),
        'track': track
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mobile-station-data/<station_id>')
def get_mobile_station_data(station_id):
    duration = int(request.args.get('duration', 1))  # Default to 1 hour if not specified
    variable = request.args.get('variable', 'none')
    with open('static/config/mobile_stations.json') as f:
        stations = json.load(f)
        station = next((s for s in stations if s['id'] == station_id), None)
        if not station:
            return jsonify({'error': 'Station not found'}), 404

    variable_name = station['variables'].get(variable) if variable != 'none' else None
    data = process_netcdf_file(station['netcdf_file'], duration, variable_name)
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
