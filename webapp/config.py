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

    # URL of the new NiceGUI app (Cadence). When set, a "Try the new app" link
    # appears in the header. A bare domain (no scheme) is normalized to https://
    # so the link never resolves relative to the current app.
    _cadence_raw = os.environ.get("CADENCE_URL", "").strip()
    CADENCE_URL = (
        _cadence_raw if (not _cadence_raw or _cadence_raw.startswith(("http://", "https://")))
        else f"https://{_cadence_raw}"
    )

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30  # 30 days
