import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import os
import requests
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import box
from datetime import datetime, timedelta

from source.maps_processing.sea_ice_map_processing import SeaIceCache

@pytest.fixture
def sea_ice_cache():
    return SeaIceCache(output_dir='./test_output/', shapefile_path='./test_shapefile/')

def test_initialization(sea_ice_cache):
    assert sea_ice_cache.output_dir == './test_output/'
    assert sea_ice_cache.shapefile_path == './test_shapefile/'



def test_create_ice_chart_geojson_recent_file(sea_ice_cache):
    with patch('os.path.getmtime', return_value=(datetime.now() - timedelta(minutes=15)).timestamp()), \
         patch('os.path.exists', return_value=True):

        geojson_path = sea_ice_cache.create_ice_chart_geojson()
        assert geojson_path == './test_output/ice_chart.geojson'
