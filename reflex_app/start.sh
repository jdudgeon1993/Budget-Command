#!/bin/bash
# Railway exposes a single PORT env var.
# Reflex needs frontend on 3000 and backend on 8000.
# We start both and put nginx in front on $PORT.

set -e

PORT="${PORT:-8080}"

# Install nginx if not present
if ! command -v nginx &> /dev/null; then
    apt-get update -qq && apt-get install -y nginx -qq
fi

# Write nginx config to unify both Reflex services on $PORT
cat > /etc/nginx/sites-enabled/default << EOF
server {
    listen ${PORT};

    # WebSocket backend (Reflex state sync)
    location /_event {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    location /ping {
        proxy_pass http://localhost:8000;
    }

    # Everything else → Next.js frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

nginx -t && nginx

# Start Reflex (manages both frontend :3000 and backend :8000)
exec reflex run --env prod --backend-host 0.0.0.0 --backend-port 8000
