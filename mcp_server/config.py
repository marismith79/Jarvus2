from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    # Availity API settings
    AVAILITY_CLIENT_ID: str
    AVAILITY_CLIENT_SECRET: str
    AVAILITY_PAYER_ID: str
    AVAILITY_TOKEN_URL: str = "https://api.availity.com/availity/v1/token"
    AVAILITY_API_BASE_URL: str = "https://api.availity.com/availity/development-partner/v1"
    
    # MCP settings
    MCP_SERVER_NAME: str = "availity"
    MCP_SERVER_VERSION: str = "1.0.0"
    MCP_SERVER_DESCRIPTION: str = "MCP server for Availity API integration"
    
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