# Cadence (NiceGUI) — self-contained service.
# In Railway, set this service's Root Directory to `cadence`. Then the build
# context is the cadence/ folder and this service uses cadence/railway.toml +
# this Dockerfile. It no longer depends on webapp/.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Context is the cadence/ folder; nest it back under a `cadence` package so the
# relative imports and `python -m cadence.main` resolve.
COPY . ./cadence/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "cadence.main"]
