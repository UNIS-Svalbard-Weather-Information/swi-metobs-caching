import json
import os
import pytest
from unittest.mock import patch

# Import folder constants from your app module.
from source.app.app import STATIC_FOLDER, LIBS_FOLDER, MAPS_FOLDER

def test_index_page(client):
    """
    Test that the home page ("/") renders correctly.
    This assumes the pages blueprint registers "/" and returns HTML containing a <title> tag.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"<title>" in response.data

@patch("source.app.app.send_from_directory")
def test_libs_route(mock_send_from_directory, client):
    """
    Test serving JavaScript libraries from the /libs/<filename> endpoint.
    """
    dummy_content = "console.log('Hello, world!');"
    mock_send_from_directory.return_value = dummy_content

    response = client.get("/libs/somelib.js")
    expected = dummy_content.encode() if isinstance(dummy_content, str) else dummy_content
    assert response.data == expected
    mock_send_from_directory.assert_called_once_with(LIBS_FOLDER, "somelib.js")



@patch("source.app.app.send_file")
def test_manifest(mock_send_file, client):
    """
    Test serving the manifest.json file from the /manifest.json endpoint.
    """
    dummy_content = "manifest content"
    mock_send_file.return_value = dummy_content

    response = client.get("/manifest.json")
    expected = dummy_content.encode() if isinstance(dummy_content, str) else dummy_content
    assert response.data == expected
    expected_path = os.path.join(STATIC_FOLDER, "manifest.json")
    mock_send_file.assert_called_once_with(expected_path)


@patch("source.app.app.os.path.exists")
@patch("source.app.app.send_file")
def test_maps_ice_chart_exists(mock_send_file, mock_exists, client):
    """
    Test that when the ice chart GeoJSON file exists,
    it is served with the correct mimetype.
    """
    dummy_geojson = '{"type": "FeatureCollection", "features": []}'
    mock_exists.return_value = True
    mock_send_file.return_value = dummy_geojson

    response = client.get("/maps/ice_chart")
    expected = dummy_geojson.encode() if isinstance(dummy_geojson, str) else dummy_geojson
    assert response.data == expected

    expected_path = os.path.join(MAPS_FOLDER, "ice_chart.geojson")
    mock_send_file.assert_called_once_with(expected_path, mimetype='application/json')


@patch("source.app.app.os.path.exists")
def test_maps_ice_chart_not_exists(mock_exists, client):
    """
    Test that if the ice chart GeoJSON file does not exist,
    the endpoint returns a 404 error with an error message.
    """
    mock_exists.return_value = False
    response = client.get("/maps/ice_chart")
    assert response.status_code == 404

    data = json.loads(response.data)
    assert "error" in data
