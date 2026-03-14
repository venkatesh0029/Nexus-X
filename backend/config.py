import os
import sys
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

class Settings(BaseSettings):
    """
    Strict environment variable validation.
    Crashing here prevents subtle runtime bugs later.
    """
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str = "local-lm-studio" # Default since we're local
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

try:
    settings = Settings()
except ValidationError as e:
    logging.critical(f"CRITICAL: Failed to validate .env configuration on startup.\n{e}")
    sys.exit(1) # Crash loudly
