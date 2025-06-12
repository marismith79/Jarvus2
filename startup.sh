#!/bin/bash

# Install requirements
pip install -r requirements.txt

# Start the application
gunicorn --bind=0.0.0.0:$PORT wsgi:app 