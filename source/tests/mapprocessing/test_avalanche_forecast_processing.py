import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import os
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import Polygon
import json

from source.maps_processing.avalanche_forecast_processing import AvalancheForecastProcessing

@pytest.fixture
def avalanche_processor():
    return AvalancheForecastProcessing(n_days_forecast=1, regions_list=['3003'])

def test_initialization(avalanche_processor):
    assert avalanche_processor.n_days_forecast == 1
    assert avalanche_processor.regions_list == ['3003']
    #assert isinstance(avalanche_processor.logger, Logger)
    assert avalanche_processor.export_directory == './maps/avalanche_forecast'

def test_binary_to_directions():
    processor = AvalancheForecastProcessing()
    assert processor._binary_to_directions('10000000') == ['N']
    assert processor._binary_to_directions('00100010') == ['E', 'W']

@patch('requests.get')
def test_fetch_region_data(mock_get, avalanche_processor):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {'Id': '3003', 'Name': 'Test Region', 'Polygon': ['30.0,40.0 31.0,41.0']}
    ]
    mock_get.return_value = mock_response

    avalanche_processor.fetch_region_data()
    assert '3003' in avalanche_processor.regions
    assert avalanche_processor.regions['3003']['name'] == 'Test Region'
    assert avalanche_processor.regions['3003']['polygon'] == [(30.0, 40.0), (31.0, 41.0)]

@patch('requests.get')
def test_fetch_forecast_data(mock_get, avalanche_processor):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            'ValidFrom': '2023-10-01T00:00:00',
            'PublishTime': '2023-09-30T23:00:00',
            'AvalancheProblems': [],
            'DangerLevelName': 'Low',
            'MainText': 'No Rating'
        }
    ]
    mock_get.return_value = mock_response

    avalanche_processor.fetch_forecast_data()
    assert 'forecast' in avalanche_processor.regions['3003']

def test_get_region(avalanche_processor):
    avalanche_processor.regions = {'3003': {'name': 'Test Region', 'polygon': [(30.0, 40.0)]}}
    region_info = avalanche_processor.get_region('3003')
    assert region_info == {'name': 'Test Region', 'polygon': [(30.0, 40.0)]}

    region_info = avalanche_processor.get_region('9999')
    assert region_info is None

# def test_clip_shapefile_with_gps_contour(avalanche_processor):
#     # Define two sets of GPS coordinates
#     gps_coordinates_1 = [(30.0, 40.0), (30.0, 41.0), (31.0, 41.0), (31.0, 40.0)]
#     gps_coordinates_2 = [(30.5, 40.5), (30.5, 41.5), (31.5, 41.5), (31.5, 40.5)]
#     coordinates_outside = [ (29.5, 40.5), (31.6, 41.1), (30.7, 39.9), (30.8, 41.6), (29.0, 42.0) ]
# 
#     # Create a mock GeoDataFrame with two polygons and a specified CRS
#     mock_gdf = gpd.GeoDataFrame({
#         'geometry': [Polygon(gps_coordinates_1), Polygon(gps_coordinates_2)]
#     }, crs="EPSG:4326")
# 
#     print(mock_gdf)
#     with patch('geopandas.read_file', return_value=mock_gdf):
#         # Perform the clipping operation with one set of coordinates
#         clipped_gdf = avalanche_processor.clip_shapefile_with_gps_contour(coordinates_outside, 'dummy_path')
# 
#         # Debugging statements to inspect the contents
#         print("Clipped GeoDataFrame:")
#         print(clipped_gdf)
# 
#         # Check if the clipped GeoDataFrame is empty and print a message
#         if clipped_gdf.empty:
#             print("Clipped GeoDataFrame is empty. Check the intersection logic.")
# 
#         # Assert that the clipped GeoDataFrame is not empty
#         assert not clipped_gdf.empty

def test_process_3003(avalanche_processor):
    with patch.object(avalanche_processor, 'fetch_region_data') as mock_fetch_region, \
         patch.object(avalanche_processor, 'fetch_forecast_data') as mock_fetch_forecast, \
         patch.object(avalanche_processor, '_create_forecast_layer_region') as mock_create_layer, \
         patch.object(avalanche_processor, 'get_region', return_value={'name': 'Test Region', 'polygon': [(30.0, 40.0)]}):

        avalanche_processor.process_3003()
        mock_fetch_region.assert_called_once()
        mock_fetch_forecast.assert_called_once()
        mock_create_layer.assert_called_once()
