import reflex as rx
import os

config = rx.Config(
    app_name="cura",
    frontend_port=3000,
    backend_port=8000,
    # In production, the frontend calls back to the same host (nginx proxies it)
    api_url=os.environ.get("RAILWAY_PUBLIC_DOMAIN", "http://localhost:8080"),
    deploy_url=os.environ.get("RAILWAY_PUBLIC_DOMAIN", "http://localhost:8080"),
)
