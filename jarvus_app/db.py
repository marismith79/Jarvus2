import os
import time
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

load_dotenv()

db = SQLAlchemy()


def init_db(app: Flask) -> None:
    """Initialize the database with the app."""
    # Get the database URI from config (already set by Config class)
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print(f"Database URI: {database_uri}")

    # Configure SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 60,
        "max_overflow": 10,
        "pool_size": 5,
        "connect_args": {
            "connect_timeout": 60,
            "timeout": 60,
            "retry_count": 3,
            "retry_interval": 10,
        },
    }

    # Initialize the database
    db.init_app(app)

    # Add event listener for connection errors
    @event.listens_for(Engine, "connect")
    def connect(dbapi_connection: Any, connection_record: Any) -> None:
        print("Database connection established")

    @event.listens_for(Engine, "checkout")
    def checkout(
        dbapi_connection: Any, connection_record: Any, connection_proxy: Any
    ) -> None:
        print("Database connection checked out")

    @event.listens_for(Engine, "disconnect")
    def disconnect(dbapi_connection: Any, connection_record: Any) -> None:
        print("Database connection disconnected")

    # Import all models to ensure they are registered with SQLAlchemy
    # This is important for Alembic to detect all tables
    with app.app_context():
        try:
            from .models.oauth import OAuthCredentials
            from .models.tool_permission import ToolPermission
            from .models.user import User
            from .models.user_tool import UserTool
            from .models.history import History
            
            print("All models imported successfully")
            
            # Test database connection
            db.engine.connect()
            print("Database connection test successful")
            
        except Exception as e:
            print(f"Database initialization warning: {str(e)}")
            # Don't raise the exception - we want the app to start even if connection fails
            # Alembic will handle schema creation