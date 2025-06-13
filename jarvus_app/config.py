import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the absolute path of the project root
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = True

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        db_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not db_uri:
            raise ValueError(
                "AZURE_SQL_CONNECTION_STRING environment variable is not set"
            )
        
        # Add timeout parameters to the connection string
        if "?" in db_uri:
            db_uri += "&timeout=60&connect_timeout=60"
        else:
            db_uri += "?timeout=60&connect_timeout=60"
        
        return db_uri

    SQLALCHEMY_TRACK_MODIFICATIONS = False
