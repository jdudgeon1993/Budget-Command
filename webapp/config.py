"""Flask config — reads the same Supabase env vars the Reflex app used."""

import os


# DEV_SEED: when true (and no Supabase creds), auto-login a fake session and
# serve sample data so the UI can be built/screenshotted locally. Never set
# this in production.
_DEV_SEED = os.environ.get("DEV_SEED", "").lower() in ("1", "true", "yes")


class Config:
    DEV_SEED = _DEV_SEED

    if _DEV_SEED:
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
        SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
    else:
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
        SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30  # 30 days
