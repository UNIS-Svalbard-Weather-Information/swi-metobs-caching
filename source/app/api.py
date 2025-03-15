import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


from flask import Blueprint, jsonify, request, current_app, send_file
import json

api = Blueprint('api', __name__)

@api.route('/station/online', methods=['GET'])
def online_stations():
    station_handler = current_app.config['STATION_HANDLER']
    station_type = request.args.get('type', 'all')
    stations = station_handler.get_cached_online_stations(type=station_type)
    return jsonify(stations), 200

@api.route('/station/offline', methods=['GET'])
def offline_stations():
    station_handler = current_app.config['STATION_HANDLER']
    station_type = request.args.get('type', 'all')
    stations = station_handler.get_cached_online_stations(type=station_type, status='offline')
    return jsonify(stations), 200

@api.route('/station/<station_id>', methods=['GET'])
def station_metadata(station_id):
    station_handler = current_app.config['STATION_HANDLER']
    station = station_handler.get_cached_station_metadata(station_id)
    if not station:
        return jsonify({"error": "Station not found"}), 404
    return jsonify(station), 200

@api.route('/station-data/<station_id>', methods=['GET'])
def realtime_data(station_id):
    station_handler = current_app.config['STATION_HANDLER']

    # Get the 'data' query parameter
    data_param = request.args.get('data')

    if data_param == 'now':
        # Fetch real-time data
        data = station_handler.get_cached_realtime_data(station_id)
        if not data:
            return jsonify({"error": "No real-time data available"}), 404
        return jsonify(data), 200

    # Check if data_param is a valid integer (including positive and negative values)
    if data_param and data_param.lstrip('+-').isdigit():
        shift = int(data_param)
        # Fetch hourly data based on the shift value
        data = station_handler.get_cached_hourly_data(station_id, shift)
        if not data:
            return jsonify({"error": f"No data available for shift {shift}"}), 404
        return jsonify(data), 200

    # Handle cases where 'data' is not 'now' and not a valid integer
    return jsonify({"error": "Invalid request"}), 400
