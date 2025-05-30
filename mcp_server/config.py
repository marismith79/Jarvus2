from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    # Availity API Configuration
    AVAILITY_CLIENT_ID: str = "dev_client_id"  # Default for development
    AVAILITY_CLIENT_SECRET: str = "dev_client_secret"  # Default for development
    AVAILITY_PAYER_ID: str = "dev_payer_id"  # Default for development
    AVAILITY_TOKEN_URL: str = "https://api.availity.com/availity/v1/token"  # Correct token URL
    AVAILITY_API_BASE_URL: str = "https://api.availity.com/v1"
    
    # Server Configuration
    APP_NAME: str = "Availity MCP Server"
    DEBUG: bool = False
    API_PREFIX: str = "/availity/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    print(f"[CONFIG DEBUG] Loaded settings: AVAILITY_TOKEN_URL={settings.AVAILITY_TOKEN_URL}")
    return settings 