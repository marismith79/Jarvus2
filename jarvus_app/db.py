import os
import time
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import enum

load_dotenv()

db = SQLAlchemy()

# Placeholder for encrypted SQLite URI (replace with SQLCipher URI in production)
DATABASE_URL = 'sqlite:///jarvus_memory.db'

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

# --- Enums ---
class EventType(enum.Enum):
    navigation = 'navigation'
    selection = 'selection'
    form_submit = 'form_submit'
    other = 'other'

class SuggestionStatus(enum.Enum):
    shown = 'shown'
    accepted = 'accepted'
    rejected = 'rejected'
    ignored = 'ignored'

class ExecutionResult(enum.Enum):
    success = 'success'
    failure = 'failure'

# --- Models ---
class ActivityEvent(Base):
    __tablename__ = 'activity_events'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(Enum(EventType))
    summary = Column(Text)
    raw_data = Column(Text, nullable=True)  # Optional, encrypted if used
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=True)

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    context_summary = Column(Text)
    events = relationship('ActivityEvent', backref='session')

class Suggestion(Base):
    __tablename__ = 'suggestions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    suggestion_type = Column(String(64))
    context_snapshot = Column(Text)
    suggested_action = Column(Text)
    status = Column(Enum(SuggestionStatus), default=SuggestionStatus.shown)
    feedback = relationship('Feedback', backref='suggestion', uselist=False)
    executions = relationship('Execution', backref='suggestion')

class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    video_path = Column(Text, nullable=True)  # Path to user-recorded video
    inferred_steps = Column(JSON)  # List of action dicts (see schema below)
    source = Column(String(32))  # 'video', 'manual', 'agent-inferred'
    description = Column(Text, nullable=True)

    # Example action schema for inferred_steps:
    # [
    #   {"type": "click", "target": "button#submit", "timestamp": 1234567890},
    #   {"type": "type", "target": "input#email", "value": "user@example.com", "timestamp": 1234567891}
    # ]

class Execution(Base):
    __tablename__ = 'executions'
    id = Column(Integer, primary_key=True)
    suggestion_id = Column(Integer, ForeignKey('suggestions.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_json = Column(JSON)  # Structured action (see schema above)
    result = Column(Enum(ExecutionResult))
    details_json = Column(JSON)  # Structured details (e.g., output, errors)

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    suggestion_id = Column(Integer, ForeignKey('suggestions.id'))
    user_response = Column(String(32))  # e.g., thumbs_up, thumbs_down
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Summarization Placeholder ---
def summarize_activity(raw_event):
    """
    Placeholder for LLM or rules-based summarization of raw events.
    Replace with actual summarization logic.
    """
    return f"Summary of: {raw_event}"

# --- CRUD Functions ---
def record_activity(event_type, raw_event, session_id=None):
    summary = summarize_activity(raw_event)
    with SessionLocal() as db:
        event = ActivityEvent(type=event_type, summary=summary, raw_data=raw_event, session_id=session_id)
        db.add(event)
        db.commit()
        return event

def record_suggestion(context_snapshot, suggestion_type, suggested_action):
    with SessionLocal() as db:
        suggestion = Suggestion(
            context_snapshot=context_snapshot,
            suggestion_type=suggestion_type,
            suggested_action=suggested_action
        )
        db.add(suggestion)
        db.commit()
        return suggestion

def record_feedback(suggestion_id, user_response, notes=None):
    with SessionLocal() as db:
        feedback = Feedback(
            suggestion_id=suggestion_id,
            user_response=user_response,
            notes=notes
        )
        db.add(feedback)
        db.commit()
        return feedback

def record_execution(suggestion_id, action_json, result, details_json=None):
    with SessionLocal() as db:
        execution = Execution(
            suggestion_id=suggestion_id,
            action_json=action_json,
            result=result,
            details_json=details_json
        )
        db.add(execution)
        db.commit()
        return execution

def get_recent_context(n=10):
    with SessionLocal() as db:
        return db.query(ActivityEvent).order_by(ActivityEvent.timestamp.desc()).limit(n).all()

def get_feedback_history():
    with SessionLocal() as db:
        return db.query(Feedback).order_by(Feedback.timestamp.desc()).all()

def get_summaries_for_context(context_query):
    with SessionLocal() as db:
        return db.query(ActivityEvent).filter(ActivityEvent.summary.contains(context_query)).all()

# --- CRUD Functions for Workflows ---
def record_workflow(user_id, video_path, inferred_steps, source, description=None):
    with SessionLocal() as db:
        workflow = Workflow(
            user_id=user_id,
            video_path=video_path,
            inferred_steps=inferred_steps,
            source=source,
            description=description
        )
        db.add(workflow)
        db.commit()
        return workflow

def get_workflow_by_id(workflow_id):
    with SessionLocal() as db:
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()

def get_all_workflows():
    with SessionLocal() as db:
        return db.query(Workflow).order_by(Workflow.created_at.desc()).all()

# --- DB Init ---
def init_db():
    Base.metadata.create_all(engine)


def get_database_url() -> str:
    """Get database URL from environment variables with fallback logic."""
    # Check for production environment first
    if os.getenv('FLASK_ENV') == 'production':
        database_url = os.getenv('AZURE_SQL_CONNECTION_STRING')
        if database_url:
            return database_url
    
    # Fall back to development/test database
    database_url = os.getenv('TEST_DATABASE_URL')
    if database_url is None:
        raise ValueError("No database URL found in environment variables. Set AZURE_SQL_CONNECTION_STRING, or TEST_DATABASE_URL")
    return database_url


def init_db(app: Flask) -> None:
    """Initialize the database with the app."""
    # Get the database URI from config (already set by Config class)
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    # print(f"Database URI: {database_uri}")

    # Configure SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 60,
        "max_overflow": 10,
        "pool_size": 5,
        "connect_args": {
            "connect_timeout": 60,
            "timeout": 60,
            "retry_count": 3,
            "retry_interval": 10,
        },
    }

    # Initialize the database
    db.init_app(app)

    # Add event listener for connection errors
    @event.listens_for(Engine, "connect")
    def connect(dbapi_connection: Any, connection_record: Any) -> None:
        print("Database connection established")

    @event.listens_for(Engine, "checkout")
    def checkout(
        dbapi_connection: Any, connection_record: Any, connection_proxy: Any
    ) -> None:
        print("Database connection checked out")

    @event.listens_for(Engine, "disconnect")
    def disconnect(dbapi_connection: Any, connection_record: Any) -> None:
        print("Database connection disconnected")

    # Import all models to ensure they are registered with SQLAlchemy
    # This is important for Alembic to detect all tables
    with app.app_context():
        try:
            from .models.oauth import OAuthCredentials
            from .models.tool_permission import ToolPermission
            from .models.user import User
            from .models.user_tool import UserTool
            from .models.history import History
            from .models.memory import ShortTermMemory, LongTermMemory, MemoryEmbedding
            
            print("All models imported successfully")
            
            # Test database connection
            db.engine.connect()
            print("Database connection test successful")
            
        except Exception as e:
            print(f"Database initialization warning: {str(e)}")
            # Don't raise the exception - we want the app to start even if connection fails
            # Alembic will handle schema creation