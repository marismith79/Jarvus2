import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = True