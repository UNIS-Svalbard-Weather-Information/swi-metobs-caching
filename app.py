"""
Flask Application for Fetching and Processing Station Data
==========================================================

This Flask application fetches and processes data from mobile and fixed stations. It exposes endpoints to retrieve station data and renders an index page.

Modules:
    flask: Flask web framework.
    json: JSON data handling.
    importlib: Dynamic importing of modules.
    sys, os: System-specific parameters and functions.

Functions:
    load_function(module_function_str)
    get_data(import_function_str, url, variables, duration, station_id)

Routes:
    /
    /api/mobile-station-data/<station_id>
    /api/fixed-station-data/<station_id>
"""

from flask import Flask, jsonify, render_template, request, send_from_directory, send_file, url_for
import json
import importlib
import sys
import os
from import_functions.sea_ice_handler import create_ice_chart_geojson
from utils.citation_utils import load_references

sys.path.append(os.path.join(os.path.dirname(__file__), './import_functions'))

app = Flask(__name__)

def load_function(module_function_str):
    """
    Dynamically loads a function from a specified module.

    Args:
        module_function_str (str): String in the format 'module_name.function_name'.

    Returns:
        function: The loaded function.
    """
    module_name, function_name = module_function_str.rsplit('.', 1)
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    return function

def get_data(import_function_str, url, variables, duration, station_id):
    """
    Fetches data using the specified import function.

    Args:
        import_function_str (str): String specifying the import function.
        url (str): URL to fetch data from.
        variables (list): List of variables to fetch.
        duration (int): Duration for which to fetch data.
        station_id (str): ID of the station.

    Returns:
        dict: Data fetched by the import function.
    """
    try:
        import_function = load_function(import_function_str)
        return import_function(url, variables, duration, station_id)
    except Exception as e:
        print(f"Error retrieving station data: {e}")
        return []

@app.route('/')
def index():
    """
    Renders the index page.

    Returns:
        str: Rendered HTML template for the index page.
    """
    return render_template('index.html')

@app.route('/api/mobile-station-data/<station_id>')
def get_mobile_station_data(station_id):
    """
    Fetches data for a specified mobile station.

    Args:
        station_id (str): ID of the mobile station.

    Query Parameters:
        duration (int, optional): Duration for which to fetch data (default is 1).

    Returns:
        Response: JSON data of the requested station or an error message.
    """
    try:
        duration = int(request.args.get('duration', 1))
        with open('static/config/mobile_stations.json') as f:
            stations = json.load(f)
            station = next((s for s in stations if s['id'] == station_id), None)
            if not station:
                return jsonify({'error': 'Station not found'}), 404

        data = get_data(station['import_function'], station['url'], station['variables'], duration, station['id'])
        
        if data==None or data == {}:
            return jsonify({'error': 'No data available'}), 404
        else:
            return jsonify(data)
    except Exception as e:
        print(f"Error retrieving station data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/fixed-station-data/<station_id>')
def get_fixed_station_data(station_id):
    """
    Fetches data for a specified fixed station.

    Args:
        station_id (str): ID of the fixed station.

    Query Parameters:
        duration (int, optional): Duration for which to fetch data (default is 1).

    Returns:
        Response: JSON data of the requested station or an error message.
    """
    try:
        duration = int(request.args.get('duration', 1))
        with open('static/config/fixed_stations.json') as f:
            stations = json.load(f)
            station = next((s for s in stations if s['id'] == station_id), None)
            if not station:
                return jsonify({'error': 'Station not found'}), 404

        data = get_data(station['import_function'], station['url'], station['variables'], duration, station['id'])
        if data==None:
            return jsonify({'error': 'No data available'}), 404
        else:
            return jsonify(data)
    except Exception as e:
        print(f"Error retrieving station data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/libs/<path:filename>')
def serve_libs(filename):
    return send_from_directory('libs', filename)

@app.route('/api/maps/sea-ice', methods=['GET'])
def serve_geojson():

    GEOJSON_FILE = create_ice_chart_geojson()
    try:
        if os.path.exists(GEOJSON_FILE):
            return send_file(GEOJSON_FILE, mimetype='application/json')
        else:
            return jsonify({"error": "GeoJSON file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/credits')
def credits():
    """
    Renders the credits page dynamically based on configuration files and .bib.
    Includes a landscape image and provider logos in place of the map, with links.
    """
    # Load references
    references = load_references()

    # Path to data provider logo directory and link file
    logo_dir = os.path.join(app.static_folder, "images/data_provider_logo")
    link_file = os.path.join(logo_dir, "link.json")

    # Load links from link.json
    try:
        with open(link_file, 'r') as f:
            logo_links = json.load(f)
    except FileNotFoundError:
        logo_links = {}

    # Dynamically fetch logos and their links
    logos = [
        {
            "src": url_for('static', filename=f'images/data_provider_logo/{file}'),
            "link": logo_links.get(file, "#")  # Default to '#' if no link is found
        }
        for file in os.listdir(logo_dir)
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))
    ]

    # Render the template
    return render_template('credits.html', references=references, logos=logos)



if __name__ == '__main__':
    #making sure the sea ice geojson is create before first loading.
    create_ice_chart_geojson()
    if not os.path.exists('data'):
        os.makedirs('data')
    app.run(debug=True)