from flask import Flask
from source.app.app import create_app

# Initialize the Flask application
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
