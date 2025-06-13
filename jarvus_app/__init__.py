from flask import Flask
from flask_login import LoginManager
from jarvus_app.routes.web_pages import web
from jarvus_app.routes.auth import auth
from jarvus_app.routes.api import api
# from jarvus_app.routes.mcp_routes import mcp_bp
from jarvus_app.routes.chatbot import chatbot_bp
from jarvus_app.routes.oauth import oauth_bp
# from jarvus_app.routes.flow_builder import flow_builder_bp
import os
from pathlib import Path
from dotenv import load_dotenv
from jarvus_app.config import Config
from .models.user import User
from .db import db  # Use the shared db instance
# Add these imports for OpenTelemetry
import logging

# Get the project root directory
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

# Load .env early only in development so Config (or your routes) can pick up env vars
if os.getenv("FLASK_ENV") == "development":
    print(f"Development mode detected: attempting to load .env file from: {env_path}")
    if env_path.exists():
        load_dotenv(env_path)
        print("Environment variables loaded from .env")
    else:
        print("Warning: .env file not found at", env_path)
else:
    print("Production mode detected: skipping .env file loading")

# Allow OAuth2 to work over HTTP in development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Remove local db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    # Secret key for session encryption
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.getenv('SECRET_KEY', 'dev'))

    logger = setup_logging()
    logger.info("Jarvus application starting up")

    # Load config
    app.config.from_object(Config)
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.signin'

    # Register user_loader
    @login_manager.user_loader
    def load_user(user_id):
        # The user is now loaded from the database
        return User.query.get(user_id)

    # Register blueprints
    app.register_blueprint(web)
    app.register_blueprint(auth)
    app.register_blueprint(api)
    # app.register_blueprint(mcp_bp, url_prefix='/mcp')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(oauth_bp)
    # app.register_blueprint(flow_builder_bp, url_prefix='/flow_builder')

    return app

import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get a logger for your app
    logger = logging.getLogger('jarvus')
    logger.setLevel(logging.INFO)
    
    # Log some startup info
    logger.info("Jarvus application starting up")
    return logger
