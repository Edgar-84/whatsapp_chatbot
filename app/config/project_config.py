import os
from pathlib import Path
from pydantic_settings import BaseSettings
from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ProjectSettings(BaseSettings):
    log_dir: str = os.path.join(BASE_DIR, "logs")
    recipes_rag_csv_path: str = os.path.join(BASE_DIR, "recipes.csv")
    account_sid: str = config("TWILIO_ACCOUNT_SID")
    auth_token: str = config("TWILIO_AUTH_TOKEN")
    twilio_number: str = config("TWILIO_NUMBER")
    DEBUG: bool = config("DEBUG", cast=bool, default=True)
    SUPABASE_URL: str = config("SUPABASE_URL")
    SUPABASE_KEY: str = config("SUPABASE_KEY")
    OPENAI_API_KEY: str = config("OPENAI_API_KEY")
    GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID")
    GOOGLE_CREDENTIAL_JSON_PATH: str = os.path.join(BASE_DIR, "client_secret.json")
    GOOGLE_TOKEN_PICKLE_PATH: str = os.path.join(BASE_DIR, "token.pickle")
    PROMPT_DIR: str = os.path.join(BASE_DIR, "prompts")

project_settings = ProjectSettings()
