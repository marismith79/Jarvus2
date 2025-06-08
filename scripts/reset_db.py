#!/usr/bin/env python
import os
from pathlib import Path
from jarvus_app import create_app
from jarvus_app.db import db

def reset_db():
    app = create_app()
    with app.app_context():
        print("Resetting database...")
        
        # Get the database file path from the URI
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Close the database connection
        db.session.close()
        
        # Remove the database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database at {db_path}")
        
        # Create new database
        db.create_all()
        print("Database reset successfully!")
        
        # Optionally populate with initial data
        if input("Would you like to populate the database with initial data? (y/n): ").lower() == 'y':
            from populate_db import populate_db
            populate_db()

if __name__ == "__main__":
    reset_db() 