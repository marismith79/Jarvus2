from flask import Flask
from jarvus_app.routes.web_pages import web
from jarvus_app.routes.auth import auth
from jarvus_app.routes.api import api
from jarvus_app.routes.mcp_routes import mcp_bp
from jarvus_app.routes.chatbot import chatbot_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "11234567890"  # replace with os.getenv or env var
    app.config["DEBUG"] = True

    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(api)
    app.register_blueprint(mcp_bp, url_prefix='/mcp')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')

    return app

def create_app_wsgi():
    return create_app()
