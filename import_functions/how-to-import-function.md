# `netcdf_boat` Function Documentation

The `netcdf_boat` function processes a NetCDF file to extract boat data over a specified duration. Users can create their own function to process more exotic data as long as they adhere to the input and output criteria described below.

## Function Signature

```python
def netcdf_boat(url, variables, duration, station_id):
```

## Inputs

### `url`
- **Type**: `str`
- **Description**: The base URL for the NetCDF file. The function uses this URL to fetch the NetCDF file for the current date or the previous day if the current date's file is not available.

### `variables`
- **Type**: `dict`
- **Description**: A dictionary mapping variable names to NetCDF variable names. These variables include:
  - `airTemperature`: The NetCDF variable name for air temperature.
  - `seaSurfaceTemperature`: The NetCDF variable name for sea surface temperature.
  - `windSpeed`: The NetCDF variable name for wind speed.
  - `windDirection`: The NetCDF variable name for wind direction.
  - `relativeHumidity`: The NetCDF variable name for relative humidity.

### `duration`
- **Type**: `int`
- **Description**: Duration in hours for which data is to be fetched. The function will process data points within this duration from the latest available data.

### `station_id`
- **Type**: `str`
- **Description**: Identifier for the station. This ID is used to name the JSON file where the processed data is saved.

## Outputs

### `data_ready`
- **Type**: `dict`
- **Description**: The processed data including the latest location, wind information, and track history. The structure of the output dictionary is as follows:
  - `lat`: Latitude of the latest data point.
  - `lon`: Longitude of the latest data point.
  - `windSpeed`: Wind speed at the latest data point.
  - `windDirection`: Wind direction at the latest data point.
  - `track`: A list of dictionaries representing the track history. Each dictionary contains:
    - `lat`: Latitude of the data point.
    - `lon`: Longitude of the data point.
    - `variable`: A dictionary of the variables specified in the input (e.g., airTemperature, seaSurfaceTemperature, etc.).
  - `latest`: A dictionary containing the latest data point with the same structure as the `variable` dictionary in the track history.

## Example

### Input

```python
url = "https://example.com/netcdf/boat_data_%Y%m%d.nc"
variables = {
    'airTemperature': 'air_temp',
    'seaSurfaceTemperature': 'sea_temp',
    'windSpeed': 'wind_spd',
    'windDirection': 'wind_dir',
    'relativeHumidity': 'rel_hum'
}
duration = 24
station_id = "station_123"
```

### Output

```json
{
  "lat": 36.7783,
  "lon": -119.4179,
  "windSpeed": 5.2,
  "windDirection": 180.0,
  "track": [
    {
      "lat": 36.7782,
      "lon": -119.4178,
      "variable": {
        "time": 1622548800.0,
        "lat": 36.7782,
        "lon": -119.4178,
        "airTemperature": 15.2,
        "seaSurfaceTemperature": 16.8,
        "windSpeed": 4.8,
        "windDirection": 170.0,
        "relativeHumidity": 60.5
      }
    },
    ...
  ],
  "latest": {
    "time": 1622552400.0,
    "lat": 36.7783,
    "lon": -119.4179,
    "airTemperature": 15.5,
    "seaSurfaceTemperature": 17.0,
    "windSpeed": 5.2,
    "windDirection": 180.0,
    "relativeHumidity": 61.0
  }
}
```

## Usage

Users can create their own function to process different types of data by following the same input and output structure. This allows for flexibility in handling various data sources while maintaining consistency in the processed output format.