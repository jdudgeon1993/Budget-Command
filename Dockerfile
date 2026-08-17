# Cadence (NiceGUI) — THE app. The root Railway service builds this from the
# repo root, so the old Flask service now runs Cadence on the same URL and data.
FROM python:3.12-slim

WORKDIR /app

COPY cadence/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Nest the package under ./cadence so relative imports and `python -m cadence.main` resolve.
COPY cadence/ ./cadence/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "cadence.main"]
