from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from jarvus_app.routes.web_pages import web
from jarvus_app.routes.auth import auth
from jarvus_app.routes.api import api
from jarvus_app.routes.mcp_routes import mcp_bp
# from jarvus_app.routes.chatbot import chatbot_bp
from jarvus_app.routes.oauth import oauth_bp
# from jarvus_app.routes.flow_builder import flow_builder_bp
import os
from dotenv import load_dotenv
from jarvus_app.config import Config
from .models.user import User
from .db import db  # Use the shared db instance

# Load .env early so Config (or your routes) can pick up env vars
load_dotenv()

# Allow OAuth2 to work over HTTP in development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Remove local db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    # Secret key for session encryption
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.getenv('SECRET_KEY', 'dev'))

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
    app.register_blueprint(mcp_bp, url_prefix='/mcp')
    # app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(oauth_bp)
    # app.register_blueprint(flow_builder_bp, url_prefix='/flow_builder')

    # Create tables
    with app.app_context():
        from .models.oauth import OAuthCredentials
        from .models.user import User
        db.create_all()
        print("Database tables created.")

    return app
