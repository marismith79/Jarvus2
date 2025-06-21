#!/usr/bin/env python
"""
Reset database using Alembic migrations.
This replaces the old manual db.drop_all() and db.create_all() approach.
"""
import os
import subprocess
import sys
from dotenv import load_dotenv

def reset_db():
    # Set environment to development by default
    os.environ.setdefault("FLASK_ENV", "development")
    load_dotenv()
    
    print("Resetting database using Alembic migrations...")
    
    try:
        # First, downgrade to base (this will drop all tables)
        print("Dropping all tables...")
        result = subprocess.run(
            ["alembic", "downgrade", "base"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            print("❌ Error dropping tables:")
            print(result.stderr)
            sys.exit(1)
        
        # Then, upgrade to head (this will recreate all tables)
        print("Recreating all tables...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("✅ Database reset successfully using Alembic!")
            print("All tables have been dropped and recreated.")
            
            # Optionally populate with initial data
            populate_choice = input("Would you like to populate the database with initial data? (y/n): ").lower()
            if populate_choice == 'y':
                print("Populating database with initial data...")
                from populate_db import populate_db
                populate_db()
                print("✅ Database populated successfully!")
        else:
            print("❌ Error recreating tables:")
            print(result.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ Error: alembic command not found. Make sure Alembic is installed.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    reset_db() 