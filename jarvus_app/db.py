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


def get_database_url() -> str:
    """Get database URL from environment variables with fallback logic."""
    # Check for production environment first
    if os.getenv('FLASK_ENV') == 'production':
        database_url = os.getenv('AZURE_SQL_CONNECTION_STRING')
        if database_url:
            return database_url
    
    # Fall back to development/test database
    database_url = os.getenv('TEST_DATABASE_URL')
    if database_url is None:
        raise ValueError("No database URL found in environment variables. Set AZURE_SQL_CONNECTION_STRING, or TEST_DATABASE_URL")
    return database_url


def init_db(app: Flask) -> None:
    """Initialize the database with the app."""
    # Get the database URI from environment variable
    raw_uri = get_database_url()
    print(f"Raw DATABASE_URI type: {type(raw_uri)}")
    print(f"Raw DATABASE_URI value: {raw_uri}")
    
    if not raw_uri:
        raise ValueError("DATABASE_URI environment variable is not set")
        
    database_uri = str(raw_uri)
    print(f"Processed DATABASE_URI: {database_uri}")

    # Add additional connection parameters
    if database_uri:
        if "?" in database_uri:
            database_uri += "&"
        else:
            database_uri += "?"
        database_uri += (
            "timeout=60&"
            "connect_timeout=60&"
            "retry_count=3&"
            "retry_interval=10&"
            "encrypt=true&"
            "trust_server_certificate=true"
        )

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

    # Create tables only if they don't exist
    with app.app_context():
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                # Import all models to ensure they are registered with SQLAlchemy
                from .models.oauth import OAuthCredentials
                from .models.tool_permission import ToolPermission
                from .models.user import User
                from .models.user_tool import UserTool
                from .models.history import History

                # This will create all tables that don't exist
                db.create_all()
                print("Database tables verified/created successfully.")

                # Verify that all required tables exist
                inspector = db.inspect(db.engine)
                required_tables = [
                    "users",
                    "google_oauth_credentials",
                    "tool_permissions",
                    "user_tools",
                    "histories",
                ]
                existing_tables = inspector.get_table_names()

                missing_tables = [
                    table
                    for table in required_tables
                    if table not in existing_tables
                ]
                if missing_tables:
                    print(
                        "Warning: The following tables are missing: "
                        f"{', '.join(missing_tables)}"
                    )
                    print("Attempting to create missing tables...")
                    db.create_all()

                break  # If successful, break the retry loop

            except OperationalError as e:
                if (
                    attempt < max_retries - 1
                ):  # Don't sleep on the last attempt
                    print(
                        f"Database connection attempt {attempt + 1} failed: "
                        f"{str(e)}"
                    )
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(
                        "Database init failed after "
                        f"{max_retries} attempts:"
                    )
                    print(str(e))
                    # Don't raise the exception - we want the app to start even if table creation fails.
                    # The tables might already exist.