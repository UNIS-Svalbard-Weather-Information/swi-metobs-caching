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
        
        r = requests.get(url, param, auth=(client_id, ''))
        
        data = []
        
        if r.status_code == 200:
            json_data = r.json()['data']
            for elem in json_data:
                data.append([
                    parser.isoparse(elem['referenceTime']),
                    [obs['value'] for obs in elem['observations'] if obs['timeResolution'] == 'PT10M'][0]
                ])
            data_dict[variable] = data
                
        else:
            print(f"Error API - {station_id}/{variable}/{duration} - {r.status_code}", end="")
            if 'error' in r.json():
                assert(r.json()['error']['code'] == r.status_code)
                print(f" - {r.json()['error']['reason']}")
            else:
                print("")
            data_dict[variable] = None
        
    # Extract all unique timestamps
    timestamps = sorted(set(chain.from_iterable(
        [entry[0] for entry in values] if values is not None else []
        for values in data_dict.values()
    )))

    # Initialize the DataFrame with the unique timestamps
    df = pd.DataFrame(index=timestamps)

    # Populate the DataFrame with data
    for key, values in data_dict.items():
        if values is not None:
            temp_df = pd.DataFrame(values, columns=['datetime', key]).set_index('datetime')
            df = df.join(temp_df, how='outer')

    # Resetting the index to have datetime as a column
    df = df.rename(columns={'index': 'datetime'})
    # Resample the DataFrame to 10-minute intervals and interpolate missing values
    df_resampled = df.resample('10T').interpolate()
        
    
    return df_resampled

def to_unix_time(dt):
    return dt.timestamp()

def metNorway_FrostAPI(url, variables, duration, station_id):
    import time

    # Get the current time in seconds since the epoch
    current_time = time.time()

    # Calculate the previous rounded 5-minute mark
    last_resquest_time = current_time - (current_time % 300)

    file_path = data_directory + station_id + "_" + str(duration) + "_" + str(last_resquest_time) + ".json"
    
    if os.path.exists(file_path):
        # If the data file already exists, load and return it
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        if duration == 0:
            work_duration=5
        df = request_data_to_FrostAPI(url, variables, work_duration, station_id)
        station = get_station_settings(station_id)
        # Creating the 'track' part
        track = []
        if duration == 0:
            pass
        else:
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

        # Creating the 'latest' part
        latest_time = df.index[-1]
        latest_row = df.iloc[-1]
        latest = {
            "time": to_unix_time(latest_time),
            "lat": station['lat'],
            "lon": station['lon']
        }
        for column in variables.keys():
            latest[column] = latest_row[column] if column in latest_row else None

        # Constructing the final dictionary
        result = {
            "lat": station['lat'],
            "lon": station['lon'],
            "windSpeed": latest["windSpeed"],
            "windDirection": latest["windDirection"],
            "track": track,
            "latest": latest
        }

        # Save the processed data to a file
        with open(file_path, 'w') as f:
            json.dump(result, f)
            
        return result
    