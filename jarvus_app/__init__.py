from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from jarvus_app.routes.web_pages import web
from jarvus_app.routes.auth import auth
from jarvus_app.routes.api import api
from jarvus_app.routes.mcp_routes import mcp_bp
from jarvus_app.routes.chatbot import chatbot_bp
from jarvus_app.routes.oauth import oauth_bp
# from jarvus_app.routes.flow_builder import flow_builder_bp
import os
from dotenv import load_dotenv
from jarvus_app.config import Config
from jarvus_app.db import db

# Load .env early so Config (or your routes) can pick up env vars
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    # Secret key for session encryption
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.getenv('SECRET_KEY', 'dev'))

    # Load config
    app.config.from_object(Config)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///jarvus.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        OAUTHLIB_INSECURE_TRANSPORT=os.getenv('FLASK_ENV') == 'development'
    )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.signin'

    # Register user_loader
    from jarvus_app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        from flask import session
        claims_dict = session.get("user_claims", {})
        claims = claims_dict.get(user_id)
        if claims:
            return User(user_id, claims)
        return None

    # Register blueprints
    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(api)
    app.register_blueprint(mcp_bp, url_prefix='/mcp')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(oauth_bp)
    # app.register_blueprint(flow_builder_bp, url_prefix='/flow_builder')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app

def create_app_wsgi():
    return create_app()
