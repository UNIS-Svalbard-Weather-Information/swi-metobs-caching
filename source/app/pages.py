import sys
import os
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


from flask import Blueprint, render_template, current_app, url_for
import os
import json
from utils.citation_utils import load_references

pages = Blueprint('pages', __name__)

def get_version_info():
    """Retrieve and format the version information from the version file."""
    version_file_path = './version'
    try:
        with open(version_file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) >= 3:
                codename = lines[0].strip()
                version = lines[1].strip()
                stage = lines[2].strip()
                return f"{codename} (build {version}) - {stage}"
            else:
                return "Version file format is incorrect"
    except Exception as e:
        return "unknown"

@pages.route('/')
def index():
    version_info = get_version_info()
    return render_template('index.html', version_info=version_info)

@pages.route('/dashboard')
def dashboard():
    git_commit_hash = get_git_commit_hash()
    return render_template('dashboard.html', git_commit_hash=git_commit_hash)

@pages.route('/credits')
def credits():
    """
    Renders the credits page dynamically based on configuration files and .bib.
    Includes a landscape image and provider logos in place of the map, with links.
    """
    git_commit_hash = get_git_commit_hash()
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
    return render_template('credits.html', references=references, logos=logos, git_commit_hash=git_commit_hash)
