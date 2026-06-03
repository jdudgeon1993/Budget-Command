#!/bin/bash
set -e

PORT="${PORT:-8080}"

exec reflex run --env prod --backend-host 0.0.0.0 --backend-port "$PORT"
