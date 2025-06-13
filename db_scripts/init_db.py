#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
import os
from dotenv import load_dotenv

# Import all models to ensure they are registered with SQLAlchemy
from jarvus_app.models.user import User
from jarvus_app.models.user_tool import UserTool

def init_db():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        print("DB file path:", db.engine.url)
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
            raise

if __name__ == "__main__":
    init_db() 