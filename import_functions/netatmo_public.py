import requests
import datetime

def netatmo_public(url, variables, duration, station_id):

    access_token = "6686beb1e582d85829086cc5|80bb323cc83a4d9b298c3d2e018eacb5"
    # Prepare the headers with the access token
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    
    # Calculate the duration time window in Unix time (seconds)
    end_time = int(datetime.datetime.now().timestamp())
    start_time = end_time - duration * 3600  # duration is given in hours, convert to seconds
    
    # Initialize result dictionary
    result = {
        'lat': None,
        'lon': None,
        'windSpeed': None,
        'windDirection': None,
        'track': [],
        'latest': {}
    }

    # Function to get data for a specific variable
    def get_data_for_variable(variable_name):
        params = {
            'device_id': station_id,
            'scale': 'max',
            'type': variables[variable_name],
            'date_begin': start_time,
            'date_end': end_time
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    # Loop through each variable and get data
    for variable_name in variables:
        data = get_data_for_variable(variable_name)
        if result['lat'] is None or result['lon'] is None:
            result['lat'] = data['body']['devices'][0]['place']['location'][0]
            result['lon'] = data['body']['devices'][0]['place']['location'][1]
        
        latest_value = data['body']['devices'][0]['dashboard_data'].get(variables[variable_name], None)
        if variable_name == 'windSpeed':
            result['windSpeed'] = latest_value
        elif variable_name == 'windDirection':
            result['windDirection'] = latest_value
        
        for record in data['body']['devices'][0]['modules']:
            track_point = next((tp for tp in result['track'] if tp['variable']['time'] == record['dashboard_data']['time_utc']), None)
            if track_point is None:
                track_point = {
                    'lat': record['dashboard_data']['location'][0],
                    'lon': record['dashboard_data']['location'][1],
                    'variable': {
                        'time': record['dashboard_data']['time_utc'],
                        'lat': record['dashboard_data']['location'][0],
                        'lon': record['dashboard_data']['location'][1],
                        'airTemperature': None,
                        'seaSurfaceTemperature': None,
                        'windSpeed': None,
                        'windDirection': None,
                        'relativeHumidity': None
                    }
                }
                result['track'].append(track_point)
            
            track_point['variable'][variable_name] = record['dashboard_data'].get(variables[variable_name], None)
    
    # Set the latest values for each variable
    for track_point in result['track']:
        if result['latest'] == {} or track_point['variable']['time'] > result['latest']['time']:
            result['latest'] = track_point['variable']
    
    return result



# Example call
url = "https://api.netatmo.com/api/getstationsdata?date_begin={start_time}&date_end={end_time}"
variables = {
    'airTemperature': 'Temperature',
    'seaSurfaceTemperature': None,
    'windSpeed': 'WindStrength',
    'windDirection': 'WindAngle',
    'relativeHumidity': 'Humidity'
}
duration = 24  # hours
station_id = "70:ee:50:1e:00:34"

# Call the function
data = netatmo_public(url, variables, duration, station_id)

print(data)
