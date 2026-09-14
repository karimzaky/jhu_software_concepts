
"""Create and configure the Flask application"""
from flask import Flask

from .pages import pages


def create_app():
    app = Flask(__name__)

    # Connecting the page routes defined in pages.py to the application.
    app.register_blueprint(pages)

    return app