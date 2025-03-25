from pydantic_settings import BaseSettings
from app.config.project_config import project_settings


class ConfigDataBase(BaseSettings):
    SUPABASE_KEY: str = project_settings.SUPABASE_KEY
    SUPABASE_URL: str = project_settings.SUPABASE_URL


settings_db = ConfigDataBase()
