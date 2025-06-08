#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
from jarvus_app.models.user import User
from jarvus_app.models.user_tool import UserTool

def populate_db():
    app = create_app()
    with app.app_context():
        print("Populating database with initial data...")
        
        # Add any initial data here
        # For example:
        # admin_user = User(id="admin", name="Admin User", email="admin@example.com")
        # db.session.add(admin_user)
        
        # Add default tools for users
        # default_tools = [
        #     UserTool(tool_name="gmail", is_active=True),
        #     UserTool(tool_name="calendar", is_active=True),
        # ]
        # db.session.add_all(default_tools)
        
        db.session.commit()
        print("Database populated successfully!")

if __name__ == "__main__":
    populate_db() 