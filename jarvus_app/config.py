import os
from pathlib import Path

from dotenv import load_dotenv

# Get the project root directory
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Load .env file FIRST to ensure it has priority
env_path = Path(basedir) / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

# Determine environment AFTER loading .env file
FLASK_ENV = os.getenv("FLASK_ENV", "development")
print(f"Running in {FLASK_ENV} mode")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = FLASK_ENV == "development"
    
    # Environment-based database configuration
    @staticmethod
    def get_database_uri():
        """Get database URI based on environment"""
        if FLASK_ENV == "production":
            db_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
            if not db_uri:
                raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set for production")
            print("Using production database (Azure SQL)")
        else:
            # Development - use TEST_DATABASE_URL or fallback to SQLite
            db_uri = os.getenv("TEST_DATABASE_URL")
            if not db_uri:
                # Fallback to SQLite in instance folder
                instance_path = Path(basedir) / "instance"
                instance_path.mkdir(exist_ok=True)
                db_uri = f"sqlite:///{instance_path}/jarvus_app.db"
                print(f"Using development SQLite database: {db_uri}")
            else:
                print("Using development database from TEST_DATABASE_URL")
        
        return db_uri
    
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    print(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # System prompt for the chatbot
    CHATBOT_SYSTEM_PROMPT = "You are a helpful assistant. Before you complete a tool call, say something to the user. After the tool call, you will see the results of the tool call, so return what the user initially asked for, based on that result."