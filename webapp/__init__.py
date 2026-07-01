"""Flask app factory for Cura (server-rendered port of the Reflex app)."""

from flask import Flask

from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from .auth import bp as auth_bp
    from .panels import bp as panels_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(panels_bp)

    # Full live mirror of the same blueprint at /proto/v4 — same routes, same
    # real data, same writes. Used to redesign one section at a time (see
    # render_panel() in panels.py) without risking or duplicating production.
    app.register_blueprint(panels_bp, name="proto", url_prefix="/proto/v4")

    # Jinja money filter — always 2 decimal places, matches $1,234.56 / -$1,234.56.
    @app.template_filter("money")
    def money(v, compact=False):
        try:
            n = float(v or 0)
        except (ValueError, TypeError):
            n = 0.0
        if compact and abs(n) >= 1000:
            return ("-$" if n < 0 else "$") + f"{abs(n) / 1000:.1f}k"
        return (f"-${abs(n):,.2f}" if n < 0 else f"${n:,.2f}")

    @app.route("/healthz")
    def healthz():
        return {"ok": True}

    return app
