# Flask app image for Railway. Build context is the repo root (see railway.toml).
FROM python:3.12-slim

WORKDIR /app

COPY webapp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp/ ./webapp/

# Railway provides $PORT. gunicorn binds to it; 2 workers is plenty to start.
ENV PYTHONUNBUFFERED=1
CMD gunicorn webapp.wsgi:app --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 60
