import os

PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-4o")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-4o-mini")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
