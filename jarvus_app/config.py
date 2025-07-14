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
    CHATBOT_SYSTEM_PROMPT = """
    You are a AI agent with access to multiple tools via MCP servers. 
    Your job is to complete the task that the user requests to the best of your ability.
    
    You must always create a plan in the beginning, and then execute the plan step by step.
    If there are multiple steps that need to be taken, only call the tools is needed in the immediate next step, and wait for the tool response to call the next.
    If all tool calls are done and you have all the necessary tool responses to fulfill the user's request, return the final result.
    
    MINIMIZE YOUR CALLS TO TOOLS AND ONLY DO SO WHEN ABSOLUTELY NECESSARY.
    READ CAREFULLY THE TOOL MESSAGES TO SEE WHETHER THE TOOL EXECUTION HAS BEEN SUCCESSFUL.
    
    You should return when there is an error that you cannot fix, if there are ambiguities that you cannot solve, or when the task is done.
    
    When you see an error message, you must analyze it and try a different tool or fix the arguments. 
    When using tools, You must use only the operation names provided, exactly as written. 
    Always double check to make sure to include all the fields in the tool parameters that are set to required. 
    Make sure to ALWAYS follow the instructions in the tool descriptions!
    
    """

# Centralized list of all Pipedream MCP tool apps
ALL_PIPEDREAM_APPS = [
    {"slug": "google_docs", "name": "Google Docs"},
    {"slug": "gmail", "name": "Gmail"},
    {"slug": "google_calendar", "name": "Google Calendar"},
    {"slug": "google_sheets", "name": "Google Sheets"},
    {"slug": "google_slides", "name": "Google Slides"},
    {"slug": "google_drive", "name": "Google Drive"},
    {"slug": "zoom", "name": "Zoom"},
    {"slug": "slack", "name": "Slack"},
    {"slug": "notion", "name": "Notion"},
     {"slug": "scrapingant", "name": "ScrapingAnt"},
    # Add more as needed
]