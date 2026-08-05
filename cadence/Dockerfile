# Cadence (NiceGUI) image for Railway — a SECOND service in the same repo.
# In Railway: New Service → same repo → set Dockerfile Path = cadence/Dockerfile,
# Docker Context = repo root. No build step, no Node — just Python.
FROM python:3.12-slim

WORKDIR /app

# Cadence reuses webapp's proven Supabase layer (webapp.db) + money math
# (webapp.formulas), so it needs both dependency sets. No gunicorn — NiceGUI
# serves its own uvicorn.
COPY webapp/requirements.txt ./webapp-requirements.txt
COPY cadence/requirements.txt ./cadence-requirements.txt
RUN pip install --no-cache-dir -r webapp-requirements.txt -r cadence-requirements.txt

COPY webapp/ ./webapp/
COPY cadence/ ./cadence/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "cadence.main"]
