from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the app."""
    # Get the database URI from environment variable
    database_uri = os.getenv("DATABASE_URI")
    
    # Add additional connection parameters
    if database_uri:
        if "?" in database_uri:
            database_uri += "&"
        else:
            database_uri += "?"
        database_uri += "timeout=60&connect_timeout=60&retry_count=3&retry_interval=10"
    
    print(f"Database URI: {database_uri}")
    
    # Configure SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 60,
        "max_overflow": 10,
        "pool_size": 5
    }
    
    # Initialize the database
    db.init_app(app)
    
    # Create tables only if they don't exist
    with app.app_context():
        try:
            # Import all models to ensure they are registered with SQLAlchemy
            from .models.user import User
            from .models.oauth import OAuthCredentials
            from .models.tool_permission import ToolPermission
            
            # This will create all tables that don't exist
            db.create_all()
            print("Database tables verified/created successfully.")
            
            # Verify that all required tables exist
            inspector = db.inspect(db.engine)
            required_tables = ['users', 'google_oauth_credentials', 'tool_permissions']
            existing_tables = inspector.get_table_names()
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                print(f"Warning: The following tables are missing: {missing_tables}")
                print("Attempting to create missing tables...")
                db.create_all()
                
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
            # Don't raise the exception - we want the app to start even if table creation fails
            # The tables might already exist
