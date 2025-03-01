import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from flask import Flask, send_from_directory, send_file, jsonify
from flask_cors import CORS
from source.app.api import api
from source.app.pages import pages

from source.cacheHandler.cacheHandler import CacheHandler
from source.maps_processing.sea_ice_map_processing import SeaIceCache

import threading
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LIBS_FOLDER = os.path.join(PROJECT_ROOT, "libs")
STATIC_FOLDER = os.path.join(PROJECT_ROOT, "static")
MAPS_FOLDER = os.path.join(PROJECT_ROOT, "maps")

PRIVATE_FILES_LIST = ['api.json']

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(PROJECT_ROOT, "templates"),
                static_folder=os.path.join(PROJECT_ROOT, "static"))
    CORS(app)

    # Initialize StationHandler once
    station_handler = CacheHandler()
    sea_ice_handler = SeaIceCache()
    app.config['STATION_HANDLER'] = station_handler

    def gather_data():
        while True:
            station_handler.cache_stations_status()
            station_handler.cache_realtime_data()
            sea_ice_handler.create_ice_chart_geojson()

            # Explicitly clean up the old instance
            old_handler = app.config['STATION_HANDLER']
            del old_handler  # Help Python garbage collect the old instance

            # Replace with a fresh instance
            app.config['STATION_HANDLER'] = CacheHandler()

            time.sleep(10 * 60)  # 10 mi

    gathering_thread = threading.Thread(target=gather_data, daemon=True)
    gathering_thread.start()

    # Register Blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(pages)

    # Serve JavaScript libraries from the libs folder
    @app.route('/libs/<path:filename>')
    def serve_libs(filename):
        return send_from_directory(LIBS_FOLDER, filename)

    # Serve static folders

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        # Split the filename by '/' and check if any part matches a restricted file
        if any(part in PRIVATE_FILES_LIST for part in filename.split('/')):
            return f"We have file not found for {filename}", 404

        return send_from_directory(STATIC_FOLDER, filename)

    @app.route('/manifest.json')
    def serve_manifest():
        return send_file(os.path.join(STATIC_FOLDER, "manifest.json"))

    @app.route('/maps/ice_chart', methods=['GET'])
    def serve_geojson():
        path = os.path.join(MAPS_FOLDER, "ice_chart.geojson")
        try:
            if os.path.exists(path):
                return send_file(path, mimetype='application/json')
            else:
                return jsonify({"error": "GeoJSON file not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/maps/avalanche_forecast/<filename>', methods=['GET'])
    def serve_geojson_avalanche(filename):
        # Append the default extension
        file_path = os.path.join(MAPS_FOLDER, f"avalanche_forecast/{filename}.geojson")
        try:
            if os.path.exists(file_path):
                return send_file(file_path, mimetype='application/json')
            else:
                return jsonify({"error": "File not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app



if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
