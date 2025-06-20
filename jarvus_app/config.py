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
    
    # Gmail API settings - Updated to most comprehensive scope
    GMAIL_SCOPES: list = [
        "https://mail.google.com/"  # Full access to Gmail account (includes all operations)
    ]
    
    # Calendar API settings - Updated to most comprehensive scope
    CALENDAR_SCOPES: list = [
        "https://www.googleapis.com/auth/calendar"  # Full access to Google Calendar
    ]
    
    # Drive API settings - Updated to most comprehensive scope
    DRIVE_SCOPES: list = [
        "https://www.googleapis.com/auth/drive"  # Full access to Google Drive
    ]
    
    # Sheets API settings - Updated to most comprehensive scope
    SHEETS_SCOPES: list = [
        "https://www.googleapis.com/auth/spreadsheets"  # Full access to Google Sheets
    ]
    
    # Docs API settings - Updated to most comprehensive scope
    DOCS_SCOPES: list = [
        "https://www.googleapis.com/auth/documents"  # Full access to Google Docs
    ]
    
    # Slides API settings - Updated to most comprehensive scope
    SLIDES_SCOPES: list = [
        "https://www.googleapis.com/auth/presentations"  # Full access to Google Slides
    ]
    
    # Combined scopes for all services
    GOOGLE_SCOPES = (
        GMAIL_SCOPES +
        CALENDAR_SCOPES +
        DRIVE_SCOPES +
        SHEETS_SCOPES +
        DOCS_SCOPES +
        SLIDES_SCOPES
    )