"""
Cura — Python Reflex rewrite of the Flask/Jinja2/JS app.

What changed:
  - Zero Jinja2 templates                → Python component functions
  - Zero manual DOM updates (refreshKpis, _refreshPanels) → Reactive state vars
  - Zero API routes                      → Event handlers on AppState
  - Zero session management              → State.access_token per-session
  - Zero htmx / fetch calls              → WebSocket state sync
  - Same Supabase backend, same formulas → 100% compatible data
"""

import reflex as rx
from .state import AppState
from .pages.login import login_page
from .pages.dashboard import dashboard_page


app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="violet"),
)

app.add_page(
    login_page,
    route="/login",
    title="Cura — Sign In",
)

app.add_page(
    login_page,
    route="/",
    title="Cura",
)

app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Cura — Dashboard",
    on_load=AppState.on_dashboard_load,
)
