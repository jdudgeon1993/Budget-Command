"""WSGI entrypoint: `gunicorn webapp.wsgi:app` (prod) or `python -m webapp.wsgi` (dev)."""

from . import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
