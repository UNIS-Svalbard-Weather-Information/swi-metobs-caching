import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


import pytest
from unittest.mock import MagicMock, patch
from source.app.api import api
from source.app.pages import pages
from source.cacheHandler.cacheHandler import CacheHandler
from source.app.app import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,  # Enable testing mode
    })

    # Mock CacheHandler
    mock_cache_handler = MagicMock()

    # Mock online stations
    mock_cache_handler.get_cached_online_stations.return_value = {
        "online_stations": [
            {
                "id": "SN99895",
                "location": {"lat": 78.9633, "lon": 11.3475},
                "name": "KVADEHUKEN II",
                "type": "Unknown"
            },
            {
                "id": "SN99763",
                "location": {"lat": 78.0648, "lon": 17.0442},
                "name": "REINDALSPASSET",
                "type": "Unknown"
            }
        ]
    }

    # Mock offline stations
    mock_cache_handler.get_cached_online_stations.side_effect = lambda **kwargs: {
        "offline_stations": [
            {
                "id": "SN99885",
                "location": {"lat": 78.38166, "lon": 14.753},
                "name": "Bohemanneset",
                "type": "Unknown"
            },
            {
                "id": "daudmannsodden",
                "location": {"lat": 78.21056, "lon": 12.98685},
                "name": "Daudmannsodden",
                "type": "Unknown"
            }
        ]
    } if kwargs.get("status") == "offline" else mock_cache_handler.get_cached_online_stations.return_value

    # Mock station metadata
    mock_cache_handler.get_cached_station_metadata.side_effect = lambda station_id: {
        "id": station_id,
        "location": {"lat": 78.5, "lon": 15.0},
        "name": f"Mock Station {station_id}",
        "type": "MockType"
    } if station_id == "12345" else None

    # Mock real-time data
    mock_cache_handler.get_cached_realtime_data.side_effect = lambda station_id: {
        "temperature": -5.0,
        "wind_speed": 10.5,
        "pressure": 1015
    } if station_id == "12345" else None

    # Mock hourly data
    mock_cache_handler.get_cached_hourly_data.side_effect = lambda station_id, shift: {
        "temperature": -6.0,
        "wind_speed": 11.0,
        "pressure": 1010
    } if station_id == "12345" else None

    # Inject the mock into the app
    app.config['STATION_HANDLER'] = mock_cache_handler

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_credits_page():
    """Mock file interactions for the credits page."""
    with patch("source.app.pages.load_references", return_value=["Mock Reference 1", "Mock Reference 2"]):
        with patch("os.listdir", return_value=["logo1.png", "logo2.jpg"]):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
                    "logo1.png": "https://provider1.com",
                    "logo2.jpg": "https://provider2.com"
                })
                yield
