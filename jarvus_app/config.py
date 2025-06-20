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
    
    # Service-specific scopes
    GMAIL_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",  # View your email messages and settings
        "https://www.googleapis.com/auth/gmail.compose",   # Manage drafts and send emails
        "https://www.googleapis.com/auth/gmail.modify"     # Read, compose and send emails from your Gmail account
    ]
    
    CALENDAR_SCOPES = [
        "https://www.googleapis.com/auth/calendar"  # See, edit, share and permanently delete all the calendars that you can access using Google Calendar
    ]
    
    DRIVE_SCOPES = [
        "https://www.googleapis.com/auth/drive",           # See, edit, create and delete all of your Google Drive files
        "https://www.googleapis.com/auth/drive.install",   # Connect itself to your Google Drive
        "https://www.googleapis.com/auth/activity"         # View the activity history of your Google apps
    ]
    
    SHEETS_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets"  # See, edit, create and delete all your Google Sheets spreadsheets
    ]
    
    DOCS_SCOPES = [
        "https://www.googleapis.com/auth/documents",  # See, edit, create and delete all your Google Docs documents
        "https://www.googleapis.com/auth/docs"        # See, edit, create and delete all of your Google Drive files
    ]
    
    SLIDES_SCOPES = [
        "https://www.googleapis.com/auth/presentations"  # See, edit, create and delete all your Google Slides presentations
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