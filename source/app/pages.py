import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


from flask import Blueprint, render_template, current_app, url_for
import os
import json
from utils.citation_utils import load_references

pages = Blueprint('pages', __name__)

@pages.route('/')
def index():
    return render_template('index.html')

@pages.route('/credits')
def credits():
    """
    Renders the credits page dynamically based on configuration files and .bib.
    Includes a landscape image and provider logos in place of the map, with links.
    """
    # Load references
    references = load_references()

    # Path to data provider logo directory and link file
    logo_dir = os.path.join(current_app.static_folder, "images/data_provider_logo")
    link_file = os.path.join(logo_dir, "link.json")

    # Load links from link.json
    try:
        with open(link_file, 'r') as f:
            logo_links = json.load(f)
    except FileNotFoundError:
        logo_links = {}

    # Dynamically fetch logos and their links
    logos = [
        {
            "src": url_for('static', filename=f'images/data_provider_logo/{file}'),
            "link": logo_links.get(file, "#")  # Default to '#' if no link is found
        }
        for file in os.listdir(logo_dir)
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))
    ]

    # Render the template
    return render_template('credits.html', references=references, logos=logos)
