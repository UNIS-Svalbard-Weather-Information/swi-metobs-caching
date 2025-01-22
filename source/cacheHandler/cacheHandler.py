import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from source.configHandler.confighandler import ConfigHandler
from source.datasource.datasourceFactory import get_datasource

from source.logger.logger import Logger

import json
from datetime import datetime
import shutil

class CacheHandler:
    def __init__(self, directory='./cache/', path_config = None, cleaning_list = None):
        self.directory = directory
        self.logger = Logger.setup_logger("CacheHandler")
        self.config = ConfigHandler()
        self.online_stations = []
        os.makedirs(self.directory, exist_ok=True)

        if path_config is None:
            self.path_config = {
                'station_status' : 'cache_stations_status.json',
                'station_metadata_single' : './000_stations_metadata/',
                'realtime_data' : './111_data_realtime/',
                'online' : './000_status_online_stations/',
                'offline': './000_status_offline_stations/',
            }
        else:
            self.path_config = path_config

        if cleaning_list is None:
            self.cleaning_list = ['online', 'offline']
        else:
            self.cleaning_list = cleaning_list

    def cache_stations_status(self):
        self.logger.info("Starting to cache station statuses...")

        stations = self.config.get_stations(type="all")
        self.logger.info(f"Retrieved {len(stations)} stations for processing.")

        state = []

        for station_id in stations:
            try:
                self.logger.debug(f"Processing station status for: {station_id}")
                datasource = get_datasource(station_id,  config=self.config)
                is_online = datasource.is_station_online(station_id)
                self.logger.debug(f"Station {station_id} online status: {'online' if is_online else 'offline'}")

                if is_online:
                    self.online_stations.append(station_id)

                metadata = self.config.get_metadata(station_id) or {}
                variables = self.config.get_variable(station_id)
                timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                infos = {
                    "id": station_id,
                    "name": metadata.get("name", "Unknown"),
                    "type": metadata.get("type", "Unknown"),
                    "location": {
                        "lat": metadata.get("lat", None),
                        "lon": metadata.get("lon", None),
                    },
                    "variables": list(variables.keys()) if variables else [],
                    "status": "online" if is_online else "offline",
                    "last_updated": timestamp or "Unknown",
                    "project" : metadata.get("project", "Unknown"),
                    "icon" : metadata.get("icon", "/static/images/red_dot.png"),
                }

                state.append(infos)
                self.logger.info(f"Successfully processed station {station_id}")

            except Exception as e:
                self.logger.error(f"Error processing station {station_id}: {e}", exc_info=True)

        self.logger.info(f"Finished caching station statuses. Total stations processed: {len(state)}")

        self._write_cache(state, self.path_config.get('station_status', 'cache_stations_status.json'))

        self._clear_cache(self.cleaning_list)

        return state

    def cache_realtime_data(self):
        """Fetches and caches real-time data for online stations."""

        self.logger.info("Starting to cache realtime data...")

        realtime_data_path = self.path_config.get('realtime_data', '/realtime_data/')

        if self.online_stations is None or len(self.online_stations) == 0:
            self.logger.info("Unknown station status. Starting collection and caching of the station status...")
            self.cache_stations_status()


        if self.online_stations is None or len(self.online_stations) == 0:
            self.logger.warning("No online stations found. Skipping data caching.")
            return


        for station in self.online_stations:
            try:
                self.logger.debug(f"Fetching real-time data for station: {station}")
                datasource = get_datasource(station,  config=self.config)

                data = datasource.fetch_realtime_data(station)

                if not data:
                    self.logger.warning(f"No data fetched for {station}, skipping cache write.")
                    continue

                filename = os.path.join(realtime_data_path, f"{station}.json")

                self._write_cache(data, filename)

                self.logger.info(f"Saved real-time data for {station} at {filename}.")

            except Exception as e:
                self.logger.error(f"Error processing real-time data for {station}: {e}", exc_info=True)

        self.logger.info("Finished caching real-time data.")

    def get_cached_online_stations(self, type="all", status='online'):
        filename = os.path.join(self.path_config.get(status, '/status_online/'), f"{type}.json")

        cached_data = self._read_cache(filename)
        if cached_data is not None:
            return cached_data

        cached_stations = self._read_cache(self.path_config.get('station_status', 'cache_stations_status.json'))

        result_list = []
        for station in cached_stations:
            if station.get('status', 'offline') == status:
                if type == "all" or station.get('type') == type:
                    result_list.append(
                        {key: station[key] for key in ["id", "name", "type", "location"] if key in station}
                    )

        result = {
            f"{status}_stations": result_list,
        }

        self._write_cache(result, filename)

        return result

    def get_cached_realtime_data(self, station_id):
        self.logger.info(f"Fetching real-time data for station ID: {station_id}")
        try:
            realtime_data_path = self.path_config.get('realtime_data', '/realtime_data/')
            filename = os.path.join(realtime_data_path, f"{station_id}.json")

            cached_data = self._read_cache(filename)
            if cached_data is None:
                self.logger.warning(f"Cache file contains no valid data for station ID {station_id}")
            else:
                self.logger.info(f"Successfully retrieved cached data for station ID {station_id}")

            return cached_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in cache file for station ID {station_id}: {e}", exc_info=True)
        except Exception as e:
            self.logger.critical(f"Unexpected error while fetching real-time data for station ID {station_id}: {e}",
                                 exc_info=True)

        return None

    def get_cached_station_metadata(self, station_id):
        self.logger.info(f"Fetching metadata for station ID: {station_id}")
        try:
            filename = os.path.join(self.path_config.get('station_metadata_single', 'stations_metadata'),
                                    f"{station_id}.json")
            cached_data = self._read_cache(filename)
            if cached_data is not None:
                return cached_data

            stations_metadata = self._read_cache(self.path_config.get('station_status', 'cache_stations_status.json'))
            if not stations_metadata:
                self.logger.warning("No station metadata found in cache.")
                return None

            for station in stations_metadata:
                if station.get('id') == station_id:
                    self._write_cache(station, filename)
                    return station

            self.logger.warning(f"Station ID {station_id} not found in metadata cache.")
            return None

        except Exception as e:
            self.logger.error(f"Unexpected error retrieving metadata for station {station_id}: {e}")
            return None


    def _clear_cache(self, entries):
        """Private method to clear cache entries, with logging."""

        self.logger.info(f"Starting cache clearing for {len(entries)} entries.")

        for entry in entries:
            file_path = self.path_config.get(entry)
            if file_path is None:
                self.logger.warning(f"No path configured for cache entry: {entry}")
                continue
            file_path = os.path.join(self.directory, file_path)

            if file_path:  # Ensure the path is valid
                self.logger.debug(f"Attempting to delete cache entry: {file_path}")
                self._delete_path(file_path)
            else:
                self.logger.warning(f"Invalid cache path for entry: {entry}")

        self.logger.info("Cache clearing completed.")


    def _write_cache(self, json_data, filename):
        """Writes a JSON dictionary to a file, ensuring subdirectories exist."""

        # Construct the full file path
        file_path = os.path.join(self.directory, filename)

        # Extract the directory path from the filename and ensure it exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=4)
            self.logger.info(f"Cache written successfully to {file_path}")
        except Exception as e:
            self.logger.error(f"Error writing cache to {file_path}: {e}", exc_info=True)

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
            return

    def _delete_path(self, path):
        """Private method to delete a file or directory recursively, with logging."""
        try:
            if os.path.isfile(path):  # Check if it's a file
                os.remove(path)
                self.logger.info(f"File deleted: {path}")
            elif os.path.isdir(path):  # Check if it's a directory
                shutil.rmtree(path)
                self.logger.info(f"Directory deleted: {path}")
            else:
                self.logger.warning(f"Path not found: {path}")
        except Exception as e:
            self.logger.error(f"Error deleting {path}: {e}", exc_info=True)
