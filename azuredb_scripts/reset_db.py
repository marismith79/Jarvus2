#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
from dotenv import load_dotenv

def reset_db():
    load_dotenv()
    app = create_app()
    with app.app_context():
        print("Resetting database...")
        
        try:
            # Drop all tables
            db.drop_all()
            print("Dropped all existing tables")
            
            # Create new tables
            db.create_all()
            print("Created new tables")
            
            # Optionally populate with initial data
            if input("Would you like to populate the database with initial data? (y/n): ").lower() == 'y':
                from populate_db import populate_db
                populate_db()
                
        except Exception as e:
            print(f"Error resetting database: {str(e)}")
            raise

if __name__ == "__main__":
    reset_db() 