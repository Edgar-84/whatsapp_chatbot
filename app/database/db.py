from app.database.supabase_client import SupabaseClient, SupabaseSettings
from app.database.db_config import settings_db


async def get_supabase_client() -> SupabaseClient:
    settings = SupabaseSettings(url=settings_db.SUPABASE_URL, key=settings_db.SUPABASE_KEY)
    await SupabaseClient.initialize(settings)
    return SupabaseClient()
