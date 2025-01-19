import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from source.configHandler.confighandler import ConfigHandler
from source.datasource.datasourceFactory import get_datasource

from source.logger.logger import Logger

import json
from datetime import datetime

class CacheHandler:
    def __init__(self, directory='./cache/'):
        self.directory = directory
        self.logger = Logger.setup_logger("CacheHandler")
        self.config = ConfigHandler()
        os.makedirs(self.directory, exist_ok=True)

    def cache_stations_status(self):
        self.logger.info("Starting to cache station statuses...")

        stations = self.config.get_stations(type="all")
        self.logger.info(f"Retrieved {len(stations)} stations for processing.")

        state = []

        for station in stations:
            try:
                self.logger.debug(f"Processing station: {station}")
                datasource = get_datasource(station)
                is_online = datasource.is_station_online(station)
                self.logger.debug(f"Station {station} online status: {'online' if is_online else 'offline'}")

                metadata = self.config.get_metadata(station) or {}
                variables = self.config.get_variable(station)
                timestamp = None

                try:
                    timestamp = datasource.fetch_realtime_data(station).get("timeseries", [{}])[0].get("timestamp")
                except Exception as e:
                    self.logger.warning(f"Could not fetch last_updated timestamp for station {station}: {e}")

                infos = {
                    "id": station,
                    "name": metadata.get("name", "Unknown"),
                    "type": metadata.get("type", "Unknown"),
                    "location": {
                        "lat": metadata.get("lat", None),
                        "lon": metadata.get("lon", None),
                    },
                    "variables": list(variables.keys()) if variables else [],
                    "status": "online" if is_online else "offline",
                    "last_updated": timestamp or "Unknown",
                }

                state.append(infos)
                self.logger.info(f"Successfully processed station {station}")

            except Exception as e:
                self.logger.error(f"Error processing station {station}: {e}", exc_info=True)

        self.logger.info(f"Finished caching station statuses. Total stations processed: {len(state)}")

        self._write_cache(state, 'cache_stations_status.json')

        return state


    def _write_cache(self, json_data, struct):
        """Writes a JSON dictionary to a file in the specified directory."""
        file_path = os.path.join(self.directory, struct)
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=4)
            self.logger.info(f"Cache written successfully to {file_path}")
        except Exception as e:
            self.logger.error(f"Error writing cache to {file_path}: {e}")

    def _read_cache(self, struct):
        """Reads a JSON dictionary from a file in the specified directory."""
        file_path = os.path.join(self.directory, struct)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Cache read successfully from {file_path}")
                return data
        except FileNotFoundError:
            self.logger.warning(f"Cache file {file_path} not found.")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON from {file_path}.")
            return None
        except Exception as e:
            self.logger.error(f"Error reading cache from {file_path}: {e}")
            return None
