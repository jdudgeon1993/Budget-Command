"""Flask config — reads the same Supabase env vars the Reflex app used."""

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

    # DEV_SEED: when true (and no Supabase creds), auto-login a fake session and
    # serve sample data so the UI can be built/screenshotted locally. Never set
    # this in production.
    DEV_SEED = os.environ.get("DEV_SEED", "").lower() in ("1", "true", "yes")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days
