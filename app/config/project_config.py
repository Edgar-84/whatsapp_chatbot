import os
from pathlib import Path
from pydantic_settings import BaseSettings
from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ProjectSettings(BaseSettings):
    log_dir: str = os.path.join(BASE_DIR, "logs")
    account_sid: str = config("TWILIO_ACCOUNT_SID")
    auth_token: str = config("TWILIO_AUTH_TOKEN")
    twilio_number: str = config("TWILIO_NUMBER")
    DEBUG: bool = config("DEBUG", cast=bool, default=True)
    SUPABASE_URL: str = config("SUPABASE_URL")
    SUPABASE_KEY: str = config("SUPABASE_KEY")

project_settings = ProjectSettings()
