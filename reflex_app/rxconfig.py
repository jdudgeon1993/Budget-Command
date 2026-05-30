import reflex as rx
import os

_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
_api_url = f"https://{_domain}" if _domain else "http://localhost:8080"

config = rx.Config(
    app_name="cura",
    api_url=_api_url,
    deploy_url=_api_url,
    state_auto_setters=True,
)
