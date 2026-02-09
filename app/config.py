import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# ==============================================================================
# CONFIGURATION SETTINGS
# ==============================================================================
# Centralized configuration using Pydantic Settings.
# - Allows loading settings from environment variables (.env file).
# - Validates types (e.g., ensuring PORT is an integer).
# - Defines defaults for easy deployment.
# ==============================================================================

class Settings(BaseSettings):
    """Configuration settings for the application."""

    # Core App Settings
    APP_NAME: str = "Corporate Local IPTV"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Network
    # Bind to 0.0.0.0 to allow access from other machines on the network.
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    # BASE_DIR is the root of the project.
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_DIR: str = os.path.join(BASE_DIR, "media")
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'iptv.db')}"

    # Streaming & Scanning
    # Allowed extensions for the media scanner.
    # Future enhancement: Add support for audio or playlist files.
    ALLOWED_EXTENSIONS: set = {".mp4", ".mkv", ".avi", ".ts", ".mov", ".webm"}

    # Load from .env file if present
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Ensure media directory exists on startup
if not os.path.exists(settings.MEDIA_DIR):
    os.makedirs(settings.MEDIA_DIR)
