import json
from unittest.mock import patch


def test_index_page(client):
    """Test the home page ('/') renders correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"<title>" in response.data  # Ensure an HTML page is returned


@patch("source.app.pages.render_template",
       return_value="<html><title>Credits</title><body>Mock Credits Page</body></html>")
@patch("source.app.pages.load_references", return_value=["Reference 1", "Reference 2"])
@patch("os.listdir", return_value=["logo1.png", "logo2.jpg"])
@patch("builtins.open", create=True)
def test_credits_page(mock_open, mock_listdir, mock_load_references, mock_render_template, client):
    """Test the credits page ('/credits') with mocked references and logos."""

    # Mock `open()` for reading link.json
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
        "logo1.png": "https://provider1.com",
        "logo2.jpg": "https://provider2.com"
    })

    response = client.get("/credits")

    assert response.status_code == 200
    assert b"<title>Credits</title>" in response.data  # Ensure an HTML page is returned
    assert b"Mock Credits Page" in response.data  # Check if template is rendered properly
