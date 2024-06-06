from flask import Flask, jsonify, render_template
import netCDF4 as nc
import numpy as np
import json
import os

app = Flask(__name__)

def process_netcdf_file(filepath):
    dataset = nc.Dataset(filepath)
    times = dataset.variables['time'][:]
    wind_speeds = dataset.variables['wind_speed_corrected'][:]
    wind_directions = dataset.variables['wind_direction_corrected'][:]
    lats = dataset.variables['latitude'][:]
    lons = dataset.variables['longitude'][:]

    data_points = []
    for i in range(len(times)):
        data_points.append({
            'time': float(times[i]),
            'lat': float(lats[i]),
            'lon': float(lons[i]),
            'windSpeed': float(wind_speeds[i]),
            'windDirection': float(wind_directions[i]),
            'windBeaufort': wind_speed_to_beaufort(float(wind_speeds[i]))
        })

    latest_data = data_points[-1]
    track = [{'lat': dp['lat'], 'lon': dp['lon']} for dp in data_points[-24:]]

    return {
        'lat': latest_data['lat'],
        'lon': latest_data['lon'],
        'windSpeed': latest_data['windSpeed'],
        'windDirection': latest_data['windDirection'],
        'windBeaufort': latest_data['windBeaufort'],
        'track': track
    }

def wind_speed_to_beaufort(speed):
    thresholds = [0.3, 1.5, 3.3, 5.5, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4, 32.6]
    for i, threshold in enumerate(thresholds):
        if speed < threshold:
            return i
    return 12

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mobile-station-data/<station_id>')
def get_mobile_station_data(station_id):
    with open('static/config/mobile_stations.json') as f:
        stations = json.load(f)
        station = next((s for s in stations if s['id'] == station_id), None)
        if not station:
            return jsonify({'error': 'Station not found'}), 404

    data = process_netcdf_file(station['netcdf_file'])
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
