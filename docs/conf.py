import os
import sys
import subprocess
import sphinx_rtd_theme

# Add the project's source directory to the path
sys.path.insert(0, os.path.abspath('../source'))


# Dynamically generate .rst files for ./source/ modules (recursive)
def run_apidoc(_):
    """Generate API documentation recursively using sphinx-apidoc."""
    source_dir = os.path.abspath('../source')  # Your source directory
    output_dir = os.path.abspath('./source')  # Where .rst files will be stored
    exclude_patterns = ['tests', '*/tests/*']  # Exclude tests and other files

    cmd = [
        'sphinx-apidoc',
        '--force',  # Overwrite existing files
        '--module-first',  # Place module docstring before submodule docs
        '--separate',  # Create separate files for each module
        '-o', output_dir,  # Output directory for .rst files
        source_dir,  # Source code directory
        *exclude_patterns  # Patterns to exclude
    ]
    print("Running sphinx-apidoc...")
    subprocess.run(cmd, check=True)


# Hook into the Sphinx build lifecycle
def setup(app):
    app.connect('builder-inited', run_apidoc)


# -- Project Information -----------------------------------------------------
project = 'SWI - Svalbard Weather Information'
copyright = '2024, Louis Pauchet (UNIS - INSA Rouen) & Contributors'
author = 'Louis Pauchet (UNIS - INSA Rouen) & Contributors'

# -- General Configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',  # Auto-generate documentation from docstrings
    'sphinx.ext.autosummary',  # Generate summary tables for modules
    'sphinx.ext.napoleon',  # Support for Google/NumPy style docstrings
    'sphinx.ext.viewcode',  # Link to source code
]

# Autosummary settings
autosummary_generate = True
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# Theme
html_theme = 'sphinx_rtd_theme'

# Ignore deprecated method
html_theme_path = []
