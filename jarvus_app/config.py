import os

from dotenv import load_dotenv
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    ChatCompletions
)

# Load environment variables
load_dotenv()

# Get the absolute path of the project root
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = True

    # Get the database URI from environment variable
    db_uri = os.getenv("AZURE_SQL_CONNECTION_STRING")
    if not db_uri:
        raise ValueError(
            "AZURE_SQL_CONNECTION_STRING environment variable is not set"
        )
    
    SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # System prompt for the chatbot
    CHATBOT_SYSTEM_PROMPT = "You are a helpful assistant. Before you complete a tool call, say something to the user. After the tool call, you will see the results of the tool call, so return what the user initially asked for, based on that result."
    