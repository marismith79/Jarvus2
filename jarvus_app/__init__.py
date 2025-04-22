from flask import Flask
from jarvus_app.config import Config  # Adjust if you rename the package

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register routes here
    from jarvus_app.routes.web_pages import web
    app.register_blueprint(web)

    return app

# Optional for CLI/WSGI-based usage
def create_app_wsgi():
    return create_app()