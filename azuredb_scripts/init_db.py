#!/usr/bin/env python
"""
Initialize database using Flask's db.create_all().
This ensures the database is created in the location Flask expects.
"""
from jarvus_app import create_app
from jarvus_app.db import db
from dotenv import load_dotenv
import os

def init_db():
    # Set environment to development by default
    os.environ.setdefault("FLASK_ENV", "development")
    load_dotenv()
    
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        
        try:
            # This will create the database file in Flask's instance directory
            db.create_all()
            print("✅ Database initialized successfully!")
            print("All tables have been created in Flask's instance directory.")
            
            # Verify the database was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created {len(tables)} tables: {', '.join(tables)}")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            raise

if __name__ == "__main__":
    init_db() 