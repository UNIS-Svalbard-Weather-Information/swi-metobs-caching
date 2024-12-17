import os
import sys
import subprocess
import sphinx_rtd_theme

# Add the project source directory to the path
sys.path.insert(0, os.path.abspath('../source'))

# Run sphinx-apidoc to regenerate .rst files for ./source/
def run_apidoc(_):
    """Generate API documentation using sphinx-apidoc."""
    source_dir = os.path.abspath('../source')
    output_dir = os.path.abspath('./source')  # Where .rst files will be stored
    exclude_patterns = ['tests', '*/tests/*']  # Exclude test directories
    cmd = [
        'sphinx-apidoc',
        '--force',            # Overwrite existing files
        '--module-first',     # Place module docstring before submodule docs
        '-o', output_dir,     # Output directory
        source_dir            # Source code directory
    ]
    subprocess.call(cmd)

# Hook into Sphinx build lifecycle
def setup(app):
    app.connect('builder-inited', run_apidoc)

# -- Project Information -----------------------------------------------------
project = 'SWI - Svalbard Weather Information'
copyright = '2024, Louis Pauchet (UNIS - INSA Rouen) & Contributors'
author = 'Louis Pauchet (UNIS - INSA Rouen) & Contributors'

# -- General Configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # Auto-generate documentation from docstrings
    'sphinx.ext.autosummary',  # Generate summary tables for modules
    'sphinx.ext.napoleon',     # Support for Google/NumPy style docstrings
    'sphinx.ext.viewcode',     # Link to source code
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# Autodoc settings
autosummary_generate = True
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# Theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
