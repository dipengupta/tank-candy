#!/usr/bin/env sh

set -eu

HOST="${FLASK_HOST:-0.0.0.0}"
PORT="${FLASK_PORT:-5000}"
WEB_SERVER="${WEB_SERVER:-flask}"
FLASK_APP_MODULE="${FLASK_APP_MODULE:-app:create_app}"
GUNICORN_APP="${GUNICORN_APP:-app:create_app()}"
GUNICORN_CONFIG="${GUNICORN_CONFIG:-gunicorn.conf.py}"
child_pid=""
restart_requested=0

start_server() {
  case "$WEB_SERVER" in
    flask)
      flask --app "$FLASK_APP_MODULE" run --host="$HOST" --port="$PORT" --debug &
      ;;
    gunicorn)
      gunicorn --config "$GUNICORN_CONFIG" --bind "$HOST:$PORT" "$GUNICORN_APP" &
      ;;
    *)
      printf 'Unsupported WEB_SERVER value: %s\n' "$WEB_SERVER" >&2
      exit 1
      ;;
  esac
  child_pid=$!
}

stop_server() {
  if [ -n "$child_pid" ] && kill -0 "$child_pid" 2>/dev/null; then
    kill "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  child_pid=""
}

handle_restart() {
  restart_requested=1
  stop_server
}

handle_exit() {
  stop_server
  exit 0
}

trap 'handle_restart' USR1
trap 'handle_exit' INT TERM

while true; do
  restart_requested=0
  start_server
  if wait "$child_pid"; then
    exit_code=0
  else
    exit_code=$?
  fi
  child_pid=""

  if [ "$restart_requested" -eq 1 ]; then
    printf '%s server restarted inside container.\n' "$WEB_SERVER"
    continue
  fi

  exit "$exit_code"
done
