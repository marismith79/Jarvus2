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
    If the task is a large one, you should break it down into multiple parts and possibly use multiple tools in a sequence before returning the final result.
    You should return when there is an error that you cannot fix, if there are ambiguities that you cannot solve, or when the task is done.
    
    When you see an error message, you must analyze it and try a different tool or fix the arguments. 
    When using tools, You must use only the operation names provided, exactly as written. 
    Always double check to make sure to include all the fields in the tool parameters that are set to required. 
    Make sure to ALWAYS follow the instructions in the tool descriptions!
    
    > For web search, you have access to two tools:
    > - google_web_search: Use this to search the web for information. It returns a list of results with URLs and snippets.
    > - http_request: Use this to fetch and read the content of a specific URL.
    >
    > When asked a question, first use google_web_search to find relevant results. Then, select the most promising URLs and use http_request to read their content. Repeat this process as needed until you have enough information to answer the user's question."""