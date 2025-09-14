# SWI Meteorological Observation Caching Service

## Overview
This service caches meteorological data from multiple sources. It is designed to run as a **cron task every 10 minutes**, ensuring up-to-date and reliable access to weather observations. The station configuration is **automatically updated** from the [swi-metobs-station-configuration](https://github.com/UNIS-Svalbard-Weather-Information/swi-metobs-station-configuration) repository.

---

## Data Structure
Cached files are stored in the `data` folder with the following organization:

### 1. Station Status
**Path:** `data/000_stations_status/`
- **Files:**
  - `all_dict.json`: Dictionary of all stations (online and offline).
  - `offline_dict.json`: Dictionary of offline stations.
  - `online_dict.json`: Dictionary of online stations.

**Example Station Record:**
```json
"949": {
    "id": "949",
    "name": "Adventdalen, Gruve 7",
    "type": "fixed",
    "location": {
        "lat": 78.15952,
        "lon": 16.0247
    },
    "variables": [
        "airTemperature",
        "windSpeed",
        "windDirection",
        "windSpeedGust"
    ],
    "status": "offline",
    "last_updated": "2025-09-14T18:08:56Z",
    "project": "Holfuy",
    "icon": "/static/images/holfuy.svg"
}
```

---

### 2. Latest Observations
**Path:** `data/000_latest_obs/latest_dict.json`
- Contains the most recent observations for each **online** station.

**Example Fixed Station Record:**
```json
"892": {
    "id": "892",
    "timeseries": [
        {
            "timestamp": "2025-09-14T18:08:12.000Z",
            "airTemperature": 1.9,
            "windSpeed": 8.9,
            "windDirection": 211,
            "windSpeedGust": 10.3,
            "relativeHumidity": 85.8
        }
    ]
}
```

**Example Mobile Station Record:**
```json
"SN77051": {
    "id": "SN77051",
    "timeseries": [
        {
            "timestamp": "2025-09-14T18:02:00.000Z",
            "airTemperature": 11.3,
            "windSpeed": 1.4,
            "windDirection": 345,
            "relativeHumidity": 90,
            "location": {
                "lat": 69.65,
                "lon": 18.9632
            }
        }
    ]
}
```

---

### 3. Hourly Data
**Path:** `data/000_hourly_data/`
- Contains 24 files (`-1` to `-24`), each representing observations for the past 24 hours following the same format than the latest data above.

---

### 4. Long Time Series
**Path:** `data/000_long_timeseries/`
- Each station has its own folder, containing **daily Parquet files** of its time series data.

---

## Technical Details
- **Atomic Writing:** Ensures no concurrent write errors.
- **Environment Variables:**
  - `SWI_HOLFUY_API_KEY`
  - `SWI_FROST_API_KEY`
- **Volume Mapping:** A volume should be mapped to the data folder (exact path to be determined).
- **Unit Testing** Most of the code is shipped with unit test from the legacy project but it have not yet been updated.
