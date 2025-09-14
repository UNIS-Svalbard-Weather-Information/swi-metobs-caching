import os
import sys

# Ensure the application directory is in the Python path
sys.path.insert(0, os.path.dirname(__file__))

from source.app.app import create_app  # Import your Flask app factory function

# Create the Flask application instance
application = create_app()

if __name__ == '__main__':
    application.run(host='127.0.0.1', port=5000, debug=True)


