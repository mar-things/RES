"""
RES — Repair Execution System
==============================
Application configuration.

Reads all settings from the .env file via python-dotenv.
This is the single source of truth for configuration values —
never hardcode settings or credentials anywhere else.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


class AppConfig:
    """
    Central configuration object.

    All values are read from the .env file at import time.
    Defaults are provided where safe to do so.
    """

    # --- Application ---
    APP_NAME: str = os.getenv("APP_NAME", "RES - Repair Execution System")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-key")
    LANGUAGE: str = os.getenv("APP_LANGUAGE", "en")  # 'en' or 'es'

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///res.db")

    # --- Photo storage ---
    PHOTO_STORAGE_PATH: Path = Path(
        os.getenv("PHOTO_STORAGE_PATH", "assets/photos")
    )

    # --- Twilio (production notifications for clients) ---
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "")
    TWILIO_SMS_FROM: str = os.getenv("TWILIO_SMS_FROM", "")

    # --- OpenAI (Cost Estimator Subproject — Phase 7) ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- Feature Flags ---
    USE_TWILIO: bool = APP_ENV == "production" and bool(TWILIO_ACCOUNT_SID)
    COST_ESTIMATOR_ENABLED: bool = False  # Enable when subproject is ready

    # --- Derived helpers ---
    IS_DEV: bool = APP_ENV == "development"
    IS_PROD: bool = APP_ENV == "production"
