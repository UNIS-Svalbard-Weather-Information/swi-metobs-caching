from flask import Flask, jsonify, render_template, request
import netCDF4 as nc
import json
import numpy as np
import json
import importlib
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), './import_functions'))

app = Flask(__name__)

def load_function(module_function_str):
    module_name, function_name = module_function_str.rsplit('.', 1)
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    return function

def get_data(import_function_str, url, variables, duration, station_id):
    import_function = load_function(import_function_str)
    return import_function(url, variables, duration, station_id)

    

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

        data = get_data(station['import_function'], station['url'], station['variables'], duration, station['id'])
        return jsonify(data)
    except Exception as e:
        print(f"Error retrieving station data: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    

@app.route('/api/fixed-station-data/<station_id>')
def get_fixed_station_data(station_id):
    try:
        duration = int(request.args.get('duration', 1))
        with open('static/config/fixed_stations.json') as f:
            stations = json.load(f)
            station = next((s for s in stations if s['id'] == station_id), None)
            if not station:
                return jsonify({'error': 'Station not found'}), 404

        data = get_data(station['import_function'], station['url'], station['variables'], duration, station['id'])
        return jsonify(data)
    except Exception as e:
        print(f"Error retrieving station data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
