# Build context is the repo root.
# All paths are relative to repo root.

# ── Stage 1: Compile the Next.js frontend ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip --no-install-recommends \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps from reflex_app/
COPY reflex_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Reflex app source
COPY reflex_app/cura/ ./cura/
COPY reflex_app/rxconfig.py .
# Static files served at root (assets/ → public/ in Next.js build)
COPY reflex_app/assets/ ./assets/

# Compile Next.js frontend into .web/
# No env vars needed at build time — all Supabase calls happen at runtime
RUN reflex export --frontend-only --no-zip \
    || (reflex init --loglevel debug && reflex export --frontend-only --no-zip)


# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip --no-install-recommends \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY reflex_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source + compiled .web/ from builder
COPY --from=builder /app .

# Start script
COPY reflex_app/start.sh /start.sh
RUN chmod +x /start.sh

ENV PYTHONUNBUFFERED=1

CMD ["/start.sh"]
