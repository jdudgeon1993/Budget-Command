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

    # Jinja money filter — matches the app's $1,234 / -$1,234 formatting.
    @app.template_filter("money")
    def money(v, compact=False):
        try:
            n = float(v or 0)
        except (ValueError, TypeError):
            n = 0.0
        if compact and abs(n) >= 1000:
            return ("-$" if n < 0 else "$") + f"{abs(n) / 1000:.1f}k"
        return (f"-${abs(n):,.0f}" if n < 0 else f"${n:,.0f}")

    @app.route("/healthz")
    def healthz():
        return {"ok": True}

    return app
