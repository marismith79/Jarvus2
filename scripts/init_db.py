#!/usr/bin/env python
from jarvus_app import create_app
from jarvus_app.db import db

def init_db():
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 