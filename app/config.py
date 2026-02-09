import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration settings for the application."""
    APP_NAME: str = "Corporate Local IPTV"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Network
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_DIR: str = os.path.join(BASE_DIR, "media")
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'iptv.db')}"

    # Streaming
    ALLOWED_EXTENSIONS: set = {".mp4", ".mkv", ".avi", ".ts", ".mov", ".webm"}

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Ensure media directory exists
if not os.path.exists(settings.MEDIA_DIR):
    os.makedirs(settings.MEDIA_DIR)
