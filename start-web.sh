#!/usr/bin/env sh

set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5000}"
GUNICORN_APP="${GUNICORN_APP:-app:create_app()}"
GUNICORN_CONFIG="${GUNICORN_CONFIG:-gunicorn.conf.py}"

exec gunicorn --config "$GUNICORN_CONFIG" --bind "$HOST:$PORT" "$GUNICORN_APP"
