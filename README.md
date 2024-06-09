# UNIS Svalbard Weather Information

UNIS Svalbard Weather Information (SWI) is an application to gather the data coming from different weather stations across the archipelago in order to have an overview of the weather conditions.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
  - [Mobile Stations](#mobile-stations)
  - [Fixed Stations](#fixed-stations)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [API Endpoints](#api-endpoints)
- [Import Functions](#import-functions)
- [Directory Structure](#directory-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the repository:**

    ```bash
    git clone <repository_url>
    ```

2. **Navigate to the project directory:**

    ```bash
    cd <project_directory>
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The application uses JSON configuration files to define the details of mobile and fixed stations.

### Mobile Stations

Example `mobile_stations.json`:

```json
[
    {
        "id": "bard",
        "name": "MS Bard",
        "project": "IWIN Boat",
        "url": "https://thredds.met.no/thredds/dodsC/met.no/observations/unis/mobile_AWS_MSBard/10min/%Y/%m/mobile_AWS_MSBard_Table_10min_%Y%m%d.nc",
        "variables": {
            "airTemperature": "temperature",
            "seaSurfaceTemperature": null,
            "windSpeed": "wind_speed_corrected",
            "windDirection": "wind_direction_corrected",
            "relativeHumidity": "relative_humidity"
        },
        "icon": "/static/images/boat/bard.png",
        "import_function" : "netcdf_boat.netcdf_boat"
    },
    ...
]
```

### Fixed Stations

Example `fixed_stations.json`:

```json
[
    {
        "id": "bohemanneset",
        "name": "Bohemanneset",
        "project": "IWIN Lighthouse",
        "url": "https://thredds.met.no/thredds/dodsC/met.no/observations/unis/lighthouse_AWS_Bohemanneset/10min/%Y/%m/lighthouse_AWS_Bohemanneset_Table_10min_%Y%m%d.nc",
        "variables": {
            "airTemperature": "temperature",
            "seaSurfaceTemperature": null,
            "windSpeed": "wind_speed_corrected",
            "windDirection": "wind_direction_corrected",
            "relativeHumidity": "relative_humidity"
        },
        "icon": "/static/images/lighthouse.png",
        "lat": 78.38166,
        "lon": 14.753,
        "import_function" : "netcdf_lighthouse.netcdf_lighthouse"
    },
    ...
]
```

## Usage

### Running the Application

To run the application in development mode, execute the following command:

```bash
python app.py
```

The application will be accessible at `http://127.0.0.1:5000/`.

### API Endpoints

#### 1. Index Page

**Route:** `/`

**Method:** GET

**Description:** Renders the `index.html` template.

#### 2. Mobile Station Data

**Route:** `/api/mobile-station-data/<station_id>`

**Method:** GET

**Description:** Fetches data for a specified mobile station.

**Query Parameters:**
- `duration` (optional, default=1): Duration for which to fetch data.

**Response:**
- `200 OK`: JSON data of the requested station.
- `404 Not Found`: If the station ID does not exist.
- `500 Internal Server Error`: If there is an error processing the request.

#### 3. Fixed Station Data

**Route:** `/api/fixed-station-data/<station_id>`

**Method:** GET

**Description:** Fetches data for a specified fixed station.

**Query Parameters:**
- `duration` (optional, default=1): Duration for which to fetch data.

**Response:**
- `200 OK`: JSON data of the requested station.
- `404 Not Found`: If the station ID does not exist.
- `500 Internal Server Error`: If there is an error processing the request.

## Import Functions

The import functions used to fetch and process data are located in the `import_functions` folder. Each function is documented within its respective module and a general documentation to help to create `import_function` dedicated to certain sources of data is availble [how-to-import-function][/import_functions/how-to-import-function.md]

## Directory Structure

```plaintext
<project_directory>/
├───data
├───import_functions
├───static
│   ├───config
│   ├───css
│   ├───images
│   │   ├───boat
│   │   ├───old_wind
│   │   └───wind
│   └───js
└───templates
```

>[!WARNING] 
>The folder ```data``` is required in order to store cached data file to reduce the calculation time on the server.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new pull request.

## License

This project is licensed under the CC0 1.0 Universal. See the LICENSE file for more details.
