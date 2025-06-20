#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
from dotenv import load_dotenv

def reset_db():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print("Resetting database...")
        print("WARNING: This script uses db.drop_all() and db.create_all() which bypasses Alembic migrations.")
        print("For production, consider using Alembic downgrade/upgrade commands instead.")
        
        try:
            # Import all models to ensure they are registered
            from jarvus_app.models.user import User
            from jarvus_app.models.user_tool import UserTool
            from jarvus_app.models.oauth import OAuthCredentials
            from jarvus_app.models.tool_permission import ToolPermission
            from jarvus_app.models.history import History
            
            # Drop all tables
            db.drop_all()
            print("Dropped all existing tables")
            
            # Create new tables
            db.create_all()
            print("Created new tables")
                
        except Exception as e:
            print(f"Error resetting database: {str(e)}")
            raise

if __name__ == "__main__":
    reset_db() 