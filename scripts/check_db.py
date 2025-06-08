#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db
from sqlalchemy import inspect

def check_db():
    app = create_app()
    with app.app_context():
        print("Checking database status...")
        
        # Get database inspector
        inspector = inspect(db.engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"\nTable: {table}")
            # Get columns
            columns = inspector.get_columns(table)
            print("Columns:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
            
            # Get row count
            result = db.session.execute(f"SELECT COUNT(*) FROM {table}")
            count = result.scalar()
            print(f"Row count: {count}")

if __name__ == "__main__":
    check_db() 