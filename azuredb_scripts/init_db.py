#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
import os
from dotenv import load_dotenv

def init_db():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        print("WARNING: This script uses db.create_all() which bypasses Alembic migrations.")
        print("For production, consider using 'make migrations' instead.")
        
        try:
            # Import all models to ensure they are registered
            from jarvus_app.models.user import User
            from jarvus_app.models.user_tool import UserTool
            from jarvus_app.models.oauth import OAuthCredentials
            from jarvus_app.models.tool_permission import ToolPermission
            from jarvus_app.models.history import History
            
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
            raise

if __name__ == "__main__":
    init_db() 