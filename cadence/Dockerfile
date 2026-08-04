# Cadence (NiceGUI) image for Railway — a SECOND service in the same repo.
# In Railway: New Service → same repo → set Dockerfile Path = cadence/Dockerfile,
# Docker Context = repo root. No build step, no Node — just Python.
FROM python:3.12-slim

WORKDIR /app

COPY cadence/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cadence/ ./cadence/

# NiceGUI serves its own uvicorn server (no gunicorn) and reads $PORT itself.
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "cadence.main"]
