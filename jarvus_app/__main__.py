import os
from dotenv import load_dotenv
from flask import Flask
from jarvus_app.config import Config
from jarvus_app.db import db

# 1) Load .env early so Config (or your routes) can pick up env vars
load_dotenv()

def create_app():
    app = Flask(__name__)
    # 2) Secret key for session encryption
    app.secret_key = os.getenv("FLASK_SECRET_KEY")  

    # 3) Load any other config (e.g. B2C settings) if you have them there
    app.config.from_object(Config)
    
    # 4) initialize SQLAlchemy
    db.init_app(app)

    # 4.5) initialize Flask-Login
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.signin'
    login_manager.init_app(app)

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

    # 5) Register all blueprints
    from jarvus_app.routes.auth import auth
    from jarvus_app.routes.web_pages import web
    from jarvus_app.routes.api import api
    from jarvus_app.routes.mcp_routes import mcp_bp
    from jarvus_app.routes.chatbot import chatbot_bp
    from jarvus_app.routes.oauth import oauth_bp
    # from jarvus_app.routes.flow_builder import flow_builder_bp

    app.register_blueprint(auth)
    app.register_blueprint(web)
    app.register_blueprint(api)
    app.register_blueprint(mcp_bp, url_prefix='/mcp')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(oauth_bp)
    # app.register_blueprint(flow_builder_bp, url_prefix='/flow_builder')

    return app

if __name__ == "__main__":
    app = create_app()
    # 7) Debug=True is fine for local testing
    app.run(host="0.0.0.0", port=5001, debug=True)
