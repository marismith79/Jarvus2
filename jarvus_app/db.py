import os
import time
from typing import Any, Optional
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import QueuePool

load_dotenv()

db = SQLAlchemy()

def check_db_connection() -> bool:
    """Check if the database connection is healthy."""
    try:
        # Try to execute a simple query
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        print(f"Database connection check failed: {str(e)}")
        db.session.rollback()
        return False

def with_db_retry(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator to retry database operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        print(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        print(f"Database operation failed after {max_retries} attempts")
                        raise last_exception
            return None
        return wrapper
    return decorator

def init_db(app: Flask) -> None:
    """Initialize the database with the app."""
    # Get the database URI from environment variable
    raw_uri = os.getenv("DATABASE_URI")
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
            "timeout=300&"  # Increased timeout
            "connect_timeout=300&"  # Increased connect timeout
            "retry_count=5&"  # Increased retry count
            "retry_interval=30&"  # Increased retry interval
            "encrypt=true&"
            "trust_server_certificate=true"
        )

    print(f"Database URI: {database_uri}")

    # Configure SQLAlchemy with improved connection pool settings
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": QueuePool,
        "pool_pre_ping": True,  # Enable connection health checks
        "pool_recycle": 1800,  # Recycle connections after 30 minutes
        "pool_timeout": 300,  # Increased pool timeout
        "max_overflow": 20,  # Increased max overflow
        "pool_size": 10,  # Increased pool size
        "connect_args": {
            "connect_timeout": 300,  # Increased connect timeout
            "timeout": 300,  # Increased timeout
            "retry_count": 5,  # Increased retry count
            "retry_interval": 30,  # Increased retry interval
        },
    }

    # Initialize the database
    db.init_app(app)

    # Add event listeners for connection management
    @event.listens_for(Engine, "connect")
    def connect(dbapi_connection: Any, connection_record: Any) -> None:
        print("Database connection established")

    @event.listens_for(Engine, "checkout")
    def checkout(dbapi_connection: Any, connection_record: Any, connection_proxy: Any) -> None:
        print("Database connection checked out")
        # Verify connection health before checkout
        if not check_db_connection():
            print("Connection health check failed during checkout")
            raise OperationalError("Connection health check failed", None, None)

    @event.listens_for(Engine, "disconnect")
    def disconnect(dbapi_connection: Any, connection_record: Any) -> None:
        print("Database connection disconnected")

    # Create tables only if they don't exist
    with app.app_context():
        @with_db_retry(max_retries=3, initial_delay=5.0)
        def create_tables():
            # Import all models to ensure they are registered with SQLAlchemy
            from .models.oauth import OAuthCredentials
            from .models.tool_permission import ToolPermission
            from .models.user import User

            # This will create all tables that don't exist
            db.create_all()
            print("Database tables verified/created successfully.")

            # Verify that all required tables exist
            inspector = db.inspect(db.engine)
            required_tables = [
                "users",
                "google_oauth_credentials",
                "tool_permissions",
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

        try:
            create_tables()
        except OperationalError as e:
            print(f"Failed to create tables after retries: {str(e)}")
            # Don't raise the exception - we want the app to start even if table creation fails.
            # The tables might already exist.
