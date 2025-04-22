from flask import Flask
from jarvus_app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register routes here
    from jarvus_app.routes.web_pages import web
    app.register_blueprint(web)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)