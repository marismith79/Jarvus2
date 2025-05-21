import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = True
    
    SQLALCHEMY_DATABASE_URI = os.getenv("AZURE_SQL_CONN")
    SQLALCHEMY_TRACK_MODIFICATIONS = False