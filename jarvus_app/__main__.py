import os
from dotenv import load_dotenv
from flask import Flask
from jarvus_app.config import Config

# 1) Load .env early so Config (or your routes) can pick up env vars
load_dotenv()

def create_app():
    app = Flask(__name__)
    # 2) Secret key for session encryption
    app.secret_key = os.getenv("FLASK_SECRET_KEY")  

    # 3) Load any other config (e.g. B2C settings) if you have them there
    app.config.from_object(Config)

    # 4) Register the auth routes first
    from jarvus_app.routes.auth import auth
    app.register_blueprint(auth)

    # 5) Then your existing web pages
    from jarvus_app.routes.web_pages import web
    app.register_blueprint(web)

    return app

if __name__ == "__main__":
    app = create_app()
    # 6) Debug=True is fine for local testing
    app.run(host="0.0.0.0", port=5001, debug=True)
