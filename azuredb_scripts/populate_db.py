#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
from jarvus_app.models.user import User
from jarvus_app.models.user_tool import UserTool
from dotenv import load_dotenv
import os

def populate_db():
    # Set environment to development by default
    os.environ.setdefault("FLASK_ENV", "development")
    load_dotenv()
    
    app = create_app()
    with app.app_context():
        print("Populating database with initial data...")
        
        try:
            # Add sample user
            admin_user = User(
                id="admin",
                name="Admin User", 
                email="admin@example.com"
            )
            db.session.add(admin_user)
            print("Added admin user")
            
            # Add default tools for admin user
            default_tools = [
                UserTool(user_id="admin", tool_name="gmail", is_active=True),
                UserTool(user_id="admin", tool_name="calendar", is_active=True),
                UserTool(user_id="admin", tool_name="drive", is_active=True),
            ]
            db.session.add_all(default_tools)
            print("Added default tools for admin user")
            
            db.session.commit()
            print("Database populated successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error populating database: {str(e)}")
            raise

if __name__ == "__main__":
    populate_db() 