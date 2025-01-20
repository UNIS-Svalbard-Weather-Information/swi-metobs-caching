import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from flask import Flask
from flask_cors import CORS
from app.api import api
from app.pages import pages

from source.cacheHandler.cacheHandler import CacheHandler

import threading
import time

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Initialize StationHandler once
    station_handler = StationHandler()
    app.config['STATION_HANDLER'] = station_handler

    # Start a separate thread for data gathering
    def gather_data():
        while True:
            station_handler.update_data()
            time.sleep(10*60)  # 10 min

    gathering_thread = threading.Thread(target=gather_data, daemon=True)
    gathering_thread.start()

    # Register Blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(pages)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
