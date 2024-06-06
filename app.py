from flask import Flask, jsonify, render_template, request
import netCDF4 as nc
import numpy as np
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

def process_netcdf_file(filepath, duration):
    dataset = nc.Dataset(filepath)
    times = dataset.variables['time'][:]
    wind_speeds = dataset.variables['wind_speed_corrected'][:]
    wind_directions = dataset.variables['wind_direction_corrected'][:]
    lats = dataset.variables['latitude'][:]
    lons = dataset.variables['longitude'][:]

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
            data_points.append({
                'time': times[i].isoformat(),
                'lat': float(lats[i]),
                'lon': float(lons[i]),
                'windSpeed': float(wind_speeds[i]),
                'windDirection': float(wind_directions[i])
            })

    if data_points:
        latest_data = data_points[-1]
    else:
        latest_data = {'lat': 0, 'lon': 0, 'windSpeed': 0, 'windDirection': 0}

    track = [{'lat': dp['lat'], 'lon': dp['lon']} for dp in data_points]

    return {
        'lat': latest_data['lat'],
        'lon': latest_data['lon'],
        'windSpeed': latest_data['windSpeed'],
        'windDirection': latest_data['windDirection'],
        'track': track
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mobile-station-data/<station_id>')
def get_mobile_station_data(station_id):
    duration = int(request.args.get('duration', 1))  # Default to 1 hour if not specified
    with open('static/config/mobile_stations.json') as f:
        stations = json.load(f)
        station = next((s for s in stations if s['id'] == station_id), None)
        if not station:
            return jsonify({'error': 'Station not found'}), 404

    data = process_netcdf_file(station['netcdf_file'], duration)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
