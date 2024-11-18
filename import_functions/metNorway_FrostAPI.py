import requests
from datetime import datetime, timedelta
import pandas as pd
from dateutil.tz import tzutc
from itertools import chain
import json
import os
from generic_functions import get_station_settings
from dateutil import parser

data_directory = "./data/"

def request_data_to_FrostAPI(url, variables, duration, station_id):
    client_id = '01e39643-4912-4b63-9bbf-26de9e5aa359'
    data_dict = {}
    now = datetime.utcnow()

    for variable in variables.keys():
        param = {
            'sources': station_id,
            'elements': variables[variable],
            'referencetime': f"{(now - timedelta(hours=duration)).isoformat()}Z/{now.isoformat()}Z"
        }

        try:
            r = requests.get(url, param, auth=(client_id, ''))
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"Request error for {station_id}/{variable}/{duration}: {e}")
            data_dict[variable] = None
            continue

        data = []

        try:
            json_data = r.json()['data']
            for elem in json_data:
                data.append([
                    parser.isoparse(elem['referenceTime']),
                    [obs['value'] for obs in elem['observations'] if obs['timeResolution'] == 'PT10M' or obs['timeResolution'] == 'PT1M' or obs['timeResolution'] == 'PT1H'][0]
                ])
            data_dict[variable] = data
        except KeyError as e:
            print(f"Key error while processing data for {station_id}/{variable}/{duration}: {e}")
            data_dict[variable] = None
        except IndexError as e:
            print(f"Index error while processing data for {station_id}/{variable}/{duration}: {e}")
            data_dict[variable] = None
        except Exception as e:
            print(f"Unexpected error while processing data for {station_id}/{variable}/{duration}: {e}")
            data_dict[variable] = None

    timestamps = sorted(set(chain.from_iterable(
        [entry[0] for entry in values] if values is not None else []
        for values in data_dict.values()
    )))

    df = pd.DataFrame(index=timestamps)

    for key, values in data_dict.items():
        if values is not None:
            temp_df = pd.DataFrame(values, columns=['datetime', key]).set_index('datetime')
            df = df.join(temp_df, how='outer')

    df = df.rename(columns={'index': 'datetime'})
    df_resampled = df.resample('10min').interpolate()

    return df_resampled

def to_unix_time(dt):
    return dt.timestamp()


def get_latest_file(data_directory, station_id, duration):
    # Define the file pattern prefix
    file_prefix = f"{station_id}_{str(duration)}"
    
    # Get the current time
    now = datetime.now()
    
    # Initialize variables to store the latest file and its modification time
    latest_file = None
    latest_mtime = None
    
    # Iterate over files in the directory
    for filename in os.listdir(data_directory):
        if filename.startswith(file_prefix) and filename.endswith(".json"):
            filepath = os.path.join(data_directory, filename)
            file_mtime = os.path.getmtime(filepath)
            file_datetime = datetime.fromtimestamp(file_mtime)
            
            # Check if the file is the latest one and within the last 2 hours
            if (latest_mtime is None or file_mtime > latest_mtime) and (now - file_datetime) <= timedelta(hours=2):
                latest_file = filepath
                latest_mtime = file_mtime
    
    return latest_file


def metNorway_FrostAPI(url, variables, duration, station_id):
    import time

    current_time = time.time()
    last_resquest_time = current_time - (current_time % 300)
    file_path = data_directory + station_id + "_" + str(duration) + "_" + str(last_resquest_time) + ".json"

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        if duration == 0:
            work_duration = 1
        else:
            work_duration = duration
        
        try:
            df = request_data_to_FrostAPI(url, variables, work_duration, station_id)
        except Exception as e:
            print(f"Error while requesting data to Frost API: {e}")
            print(f"Return last stored file for {station_id}")
            return get_latest_file(data_directory, station_id, duration)
        
        try:
            station = get_station_settings(station_id)
        except Exception as e:
            print(f"Error getting station settings for {station_id}: {e}")
            return None

        track = []
        
        if duration != 0:
            for idx, row in df.iterrows():
                entry = {
                    "lat": station['lat'],
                    "lon": station['lon'],
                    "variable": {
                        "time": to_unix_time(idx),
                        "lat": station['lat'],
                        "lon": station['lon']
                    }
                }
                for column in variables.keys():
                    entry["variable"][column] = row[column] if column in row else None
                track.append(entry)

        latest_time = df.index[-1]
        latest_row = df.iloc[-1]
        latest = {
            "time": to_unix_time(latest_time),
            "lat": station['lat'],
            "lon": station['lon']
        }
        for column in variables.keys():
            latest[column] = latest_row[column] if column in latest_row else None

        result = {
            "lat": station['lat'],
            "lon": station['lon'],
            "windSpeed": latest.get("windSpeed"),
            "windDirection": latest.get("windDirection"),
            "track": track,
            "latest": latest
        }

        try:
            with open(file_path, 'w') as f:
                json.dump(result, f)
        except IOError as e:
            print(f"IO error while saving data to file: {e}")

        return result
