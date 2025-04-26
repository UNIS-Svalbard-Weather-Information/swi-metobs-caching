import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import os
import requests
from unittest.mock import patch, MagicMock
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

from source.maps_processing.maps_caching import MapsCaching

@pytest.fixture
def maps_caching():
    return MapsCaching(path='./test_maps/', force=True)

def test_initialization(maps_caching):
    assert maps_caching.path == './test_maps/'
    assert maps_caching.force is True
    assert maps_caching.DEM_path is None
    assert maps_caching.steepness_raster_path is None
    assert maps_caching.contour_path is None

@patch('os.listdir')
def test_find_existing_DEM(mock_listdir, maps_caching):
    mock_listdir.return_value = ['DTM50_DEM_example.tif']
    dem_path = maps_caching._find_existing_DEM()
    assert dem_path == './test_maps/managed/DTM50_DEM_example.tif'

@patch('os.path.exists')
def test_find_existing_steepness_raster(mock_exists, maps_caching):
    mock_exists.return_value = True
    raster_path = maps_caching._find_existing_steepness_raster()
    assert raster_path == './test_maps/managed/DTM50_steepness_raster.tif'

@patch('os.listdir')
def test_find_existing_contour(mock_listdir, maps_caching):
    mock_listdir.return_value = ['steepness_contour_example.shp']
    contour_path = maps_caching._find_existing_contour()
    assert contour_path == './test_maps/managed/steepness_contour_example.shp'


def test_get_DEM(maps_caching):
    with patch.object(maps_caching, '_download_DEM') as mock_download:
        maps_caching.get_DEM('DTM50')
        mock_download.assert_called_once_with('DTM50')

def test_get_steepness_raster(maps_caching):
    with patch.object(maps_caching, '_compute_steepness_raster') as mock_compute:
        maps_caching.get_steepness_raster('DTM50')
        mock_compute.assert_called_once_with('DTM50')

def test_get_aspect_raster(maps_caching):
    with patch.object(maps_caching, '_compute_aspect_raster') as mock_compute:
        maps_caching.get_aspect_raster('DTM50')
        mock_compute.assert_called_once_with('DTM50')

def test_get_steepness_contour(maps_caching):
    with patch.object(maps_caching, '_create_steepness_contour') as mock_create:
        maps_caching.get_steepness_contour(25, 55, 'DTM50')
        mock_create.assert_called_once()

def test_get_steepness_contour_direction(maps_caching):
    with patch.object(maps_caching, '_create_steepness_contour') as mock_create:
        maps_caching.get_steepness_contour_direction('N')
        mock_create.assert_called_once()
