import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the absolute path of the project root
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = True
    
    # Use an absolute path for the database to avoid ambiguity
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'dev.db')}"
    
        # Azure SQL Database connection string
    SQLALCHEMY_DATABASE_URI = os.getenv("AZURE_SQL_CONNECTION_STRING")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False