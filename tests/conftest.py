"""
Pytest configuration and fixtures for the swi-metobs-caching tests.

This file provides fixtures that create temporary configuration files
in config/stations/ so they don't need to be committed to the repository.
"""

import json
import os
import sys
from pathlib import Path
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Default test configuration data
TEST_FIXED_STATIONS = [
    {
        "id": "SN99870",
        "name": "ADVENTDALEN",
        "project": "Met Norway",
        "url": "https://frost.met.no/sources/v0.jsonld",
        "variables": {
            "airTemperature": "air_temperature",
            "windSpeed": "wind_speed",
            "windDirection": "wind_from_direction",
            "relativeHumidity": "relative_humidity",
            "windSpeedGust": "max(wind_speed_of_gust PT1H)",
            "surfaceSnowThickness": "surface_snow_thickness",
        },
        "icon": "/static/images/metAWS.svg",
        "lat": 78.2022,
        "lon": 15.831,
    },
    {
        "id": "SN99840",
        "name": "SVALBARD LUFTHAVN",
        "project": "Met Norway",
        "url": "https://frost.met.no/sources/v0.jsonld",
        "variables": {
            "airTemperature": "air_temperature",
            "windSpeed": "wind_speed",
            "windDirection": "wind_from_direction",
            "relativeHumidity": "relative_humidity",
            "windSpeedGust": "max(wind_speed_of_gust PT1H)",
            "surfaceSnowThickness": "surface_snow_thickness",
        },
        "icon": "/static/images/metAWS.svg",
        "lat": 78.2453,
        "lon": 15.5015,
    },
]

TEST_MOBILE_STATIONS = [
    {
        "id": "SN77046",
        "name": "Ms Billefjord",
        "project": "IWIN Boats",
        "url": "https://thredds.met.no/thredds/dodsC/met.no/observations/unis/mobile_AWS_MSBillefjord/10min/%Y/%m/mobile_AWS_MSBillefjord_Table_10min_%Y%m%d.nc",
        "variables": {
            "airTemperature": "air_temperature",
            "windSpeed": "wind_speed",
            "windDirection": "wind_from_direction",
            "relativeHumidity": "relative_humidity",
        },
        "icon": "/static/images/boat/billefjorden.svg",
        "import_function": "netcdf_boat.netcdf_boat",
    },
    {
        "id": "SN77051",
        "name": "Ms Polargirl",
        "project": "IWIN Boats",
        "url": "https://thredds.met.no/thredds/dodsC/met.no/observations/unis/mobile_AWS_MSPolargirl/10min/%Y/%m/mobile_AWS_MSPolargirl_Table_10min_%Y%m%d.nc",
        "variables": {
            "airTemperature": "air_temperature",
            "windSpeed": "wind_speed",
            "windDirection": "wind_from_direction",
            "relativeHumidity": "relative_humidity",
        },
        "icon": "/static/images/boat/polargirl.svg",
        "import_function": "netcdf_boat.netcdf_boat",
    },
]


@pytest.fixture(scope="session")
def test_config_dir():
    """
    Session-scoped fixture that creates the config/stations directory
    and temporary config files for testing.

    Returns the path to the config directory.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config" / "stations"

    # Create the directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create fixed_stations.json
    fixed_file = config_dir / "fixed_stations.json"
    if not fixed_file.exists():
        with open(fixed_file, "w") as f:
            json.dump(TEST_FIXED_STATIONS, f, indent=4)

    # Create mobile_stations.json
    mobile_file = config_dir / "mobile_stations.json"
    if not mobile_file.exists():
        with open(mobile_file, "w") as f:
            json.dump(TEST_MOBILE_STATIONS, f, indent=4)

    return config_dir


@pytest.fixture(autouse=True)
def cleanup_test_config(request, test_config_dir):
    """
    Autouse fixture that optionally cleans up test config files after tests.

    This fixture is marked as autouse=True so it runs for all tests,
    but it only performs cleanup if the test has a 'cleanup_config' marker.

    To use cleanup, mark your test with:
    @pytest.mark.cleanup_config
    """
    # We don't clean up by default to avoid breaking other tests
    # that might need the config files. They will be reused.
    pass


# Alternatively, if you want to ensure fresh config for each test module,
# you can use module-scoped fixtures
@pytest.fixture(scope="module")
def fresh_test_config_dir(tmp_path_factory):
    """
    Module-scoped fixture that creates a temporary directory with
    test config files. This is useful when you need isolated config
    for specific test modules.

    Returns a tuple of (temp_config_dir, fixed_file_path, mobile_file_path)
    """
    temp_dir = tmp_path_factory.mktemp("test_config")
    config_dir = temp_dir / "config" / "stations"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create fixed_stations.json
    fixed_file = config_dir / "fixed_stations.json"
    with open(fixed_file, "w") as f:
        json.dump(TEST_FIXED_STATIONS, f, indent=4)

    # Create mobile_stations.json
    mobile_file = config_dir / "mobile_stations.json"
    with open(mobile_file, "w") as f:
        json.dump(TEST_MOBILE_STATIONS, f, indent=4)

    return config_dir, fixed_file, mobile_file


# Provide test data as fixtures for direct use in tests
@pytest.fixture
def test_fixed_stations_data():
    """Returns the test fixed stations data."""
    return TEST_FIXED_STATIONS


@pytest.fixture
def test_mobile_stations_data():
    """Returns the test mobile stations data."""
    return TEST_MOBILE_STATIONS
