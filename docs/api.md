# Stations API Documentation

This documentation provides details on the Stations API endpoints for retrieving station status, metadata, and real-time data. Use these endpoints to get lists of online or offline stations, detailed station information, and the latest available measurement data.

---

## Base URL

All endpoints are relative to your server's base URL. For example, if your API is hosted at `http://your-server.com`, the base URL for the API will be:

```
http://your-server.com/
```

*Note:* Replace `your-server.com` with your actual domain or IP address.

---

## Endpoints

### GET `/api/station/online`

**Description:**  
Retrieves a list of all online stations.

**URL:**

```
/api/station/online
```

**HTTP Method:** `GET`

**Optional Query Parameter:**

| Parameter | Type   | Description                                      | Default |
|-----------|--------|--------------------------------------------------|---------|
| `type`    | String | Filter by station type (e.g., `"fixed"`). Use `"all"` to return all types. | `all`   |

**Response Format:** JSON

**Example Response:**

```json
{
  "online_stations": [
    {
      "icon": "/static/images/lighthouse.png",
      "id": "SN99885",
      "location": {
        "lat": 78.38166,
        "lon": 14.753
      },
      "name": "Bohemanneset",
      "project": "IWIN Lighthouse",
      "status": "online",
      "type": "fixed",
      "variables": [
        "airTemperature",
        "seaSurfaceTemperature",
        "windSpeed",
        "windDirection",
        "relativeHumidity"
      ]
    },
    {
      "icon": "/static/images/metAWS.png",
      "id": "SN99895",
      "location": {
        "lat": 78.9633,
        "lon": 11.3475
      },
      "name": "KVADEHUKEN II",
      "project": "Met Norway",
      "status": "online",
      "type": "fixed",
      "variables": [
        "airTemperature",
        "seaSurfaceTemperature",
        "windSpeed",
        "windDirection",
        "relativeHumidity"
      ]
    }
  ]
}
```

**Response Fields:**

| Field              | Type    | Description                                               |
|--------------------|---------|-----------------------------------------------------------|
| `online_stations`  | Array   | A list of online station objects.                       |
| `icon`             | String  | URL or path to the station’s icon image.                |
| `id`               | String  | Unique identifier for the station.                      |
| `location`         | Object  | Contains geographical coordinates.                      |
| &nbsp;&nbsp;`lat`  | Number  | Latitude coordinate.                                      |
| &nbsp;&nbsp;`lon`  | Number  | Longitude coordinate.                                     |
| `name`             | String  | Name of the station.                                      |
| `project`          | String  | The project with which the station is associated.       |
| `status`           | String  | Station status (will be `"online"`).                      |
| `type`             | String  | Type of station (e.g., `"fixed"`).                        |
| `variables`        | Array   | List of variables measured by the station.              |

---

### GET `/api/station/offline`

**Description:**  
Retrieves a list of all offline stations.

**URL:**

```
/api/station/offline
```

**HTTP Method:** `GET`

**Optional Query Parameter:**

| Parameter | Type   | Description                                      | Default |
|-----------|--------|--------------------------------------------------|---------|
| `type`    | String | Filter by station type (e.g., `"fixed"`). Use `"all"` to return all types. | `all`   |

**Response Format:** JSON

**Example Response:**

```json
{
  "offline_stations": [
    {
      "icon": "/static/images/lighthouse.png",
      "id": "daudmannsodden",
      "location": {
        "lat": 78.21056,
        "lon": 12.98685
      },
      "name": "Daudmannsodden",
      "project": "IWIN Lighthouse",
      "status": "offline",
      "type": "fixed",
      "variables": [
        "airTemperature",
        "seaSurfaceTemperature",
        "windSpeed",
        "windDirection",
        "relativeHumidity"
      ]
    },
    {
      "icon": "/static/images/lighthouse.png",
      "id": "narveneset",
      "location": {
        "lat": 78.56343,
        "lon": 16.29687
      },
      "name": "Narveneset",
      "project": "IWIN Lighthouse",
      "status": "offline",
      "type": "fixed",
      "variables": [
        "airTemperature",
        "seaSurfaceTemperature",
        "windSpeed",
        "windDirection",
        "relativeHumidity"
      ]
    },
    {
      "icon": "/static/images/lighthouse.png",
      "id": "kappthordsen",
      "location": {
        "lat": 78.45632,
        "lon": 15.46768
      },
      "name": "Kapp Thordsen",
      "project": "IWIN Lighthouse",
      "status": "offline",
      "type": "fixed",
      "variables": [
        "airTemperature",
        "seaSurfaceTemperature",
        "windSpeed",
        "windDirection",
        "relativeHumidity"
      ]
    }
  ]
}
```

**Response Fields:**  
The fields are the same as for the online stations, with `status` set to `"offline"`.

---

### GET `/api/station/<station_id>`

**Description:**  
Retrieves detailed metadata for a specific station identified by `<station_id>`.

**URL:**

```
/api/station/<station_id>
```

**HTTP Method:** `GET`

**URL Parameter:**

| Parameter    | Type   | Description                                               |
|--------------|--------|-----------------------------------------------------------|
| `station_id` | String | Unique identifier for the station (e.g., `SN99895`).      |

**Response Format:** JSON

**Example Response:**

```json
{
  "icon": "/static/images/metAWS.png",
  "id": "SN99895",
  "last_updated": "2025-02-08T17:32:17Z",
  "location": {
    "lat": 78.9633,
    "lon": 11.3475
  },
  "name": "KVADEHUKEN II",
  "project": "Met Norway",
  "status": "online",
  "type": "fixed",
  "variables": [
    "airTemperature",
    "seaSurfaceTemperature",
    "windSpeed",
    "windDirection",
    "relativeHumidity"
  ]
}
```

**Response Fields:**

| Field              | Type    | Description                                                  |
|--------------------|---------|--------------------------------------------------------------|
| `icon`             | String  | URL or path to the station’s icon image.                     |
| `id`               | String  | Unique identifier for the station.                           |
| `last_updated`     | String  | Timestamp (ISO 8601 format) of the last update.              |
| `location`         | Object  | Contains geographical coordinates.                           |
| &nbsp;&nbsp;`lat`  | Number  | Latitude coordinate.                                           |
| &nbsp;&nbsp;`lon`  | Number  | Longitude coordinate.                                          |
| `name`             | String  | Name of the station.                                           |
| `project`          | String  | Associated project name.                                       |
| `status`           | String  | Current station status (e.g., `"online"` or `"offline"`).      |
| `type`             | String  | Type of station (e.g., `"fixed"`).                             |
| `variables`        | Array   | List of variables measured by the station.                   |

---

### GET `/api/station-data/<station_id>?data=now`

**Description:**  
Retrieves the latest real-time measurement data for a specific station identified by `<station_id>`.  
**Note:** Currently, only the `data=now` query parameter is supported.

**URL:**

```
/api/station-data/<station_id>?data=now
```

**HTTP Method:** `GET`

**URL Parameter:**

| Parameter    | Type   | Description                                             |
|--------------|--------|---------------------------------------------------------|
| `station_id` | String | Unique identifier for the station (e.g., `SN99895`).    |

**Query Parameter:**

| Parameter | Type   | Description                                                     | Allowed Value |
|-----------|--------|-----------------------------------------------------------------|---------------|
| `data`    | String | Indicates the type of data requested. Currently only real-time data is supported. | `now`         |

**Response Format:** JSON

**Example Response:**

```json
{
  "id": "SN99895",
  "timeseries": [
    {
      "airTemperature": -5.4,
      "timestamp": "2025-02-08T17:00:00.000Z",
      "windDirection": 205,
      "windSpeed": 7.1
    }
  ]
}
```

**Response Fields:**

| Field           | Type   | Description                                                    |
|-----------------|--------|----------------------------------------------------------------|
| `id`            | String | Unique identifier for the station.                           |
| `timeseries`    | Array  | A list of measurement records.                                 |
| &nbsp;&nbsp;`airTemperature` | Number | Measured air temperature (e.g., in °C).                  |
| &nbsp;&nbsp;`timestamp`      | String | ISO 8601 formatted timestamp when the measurement was taken. |
| &nbsp;&nbsp;`windDirection`  | Number | Wind direction in degrees.                               |
| &nbsp;&nbsp;`windSpeed`      | Number | Wind speed (units as defined by your implementation).     |

**Error Cases:**

- If no real-time data is available for the station, a **404 Not Found** response is returned with a message:
  
  ```json
  { "error": "No real-time data available" }
  ```
  
- If the query parameter `data` is missing or not equal to `now`, a **400 Bad Request** response is returned:
  
  ```json
  { "error": "Invalid request" }
  ```

---

## Error Handling

The API returns standard HTTP status codes for error cases:

- **400 Bad Request:**  
  Returned when required parameters are missing or invalid.

- **404 Not Found:**  
  Returned when the specified station or data is not found.

- **500 Internal Server Error:**  
  Returned for unexpected server errors.