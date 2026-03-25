#!/usr/bin/env sh

set -eu

HOST="${FLASK_HOST:-0.0.0.0}"
PORT="${FLASK_PORT:-5000}"
child_pid=""
restart_requested=0

start_server() {
  flask --app app run --host="$HOST" --port="$PORT" --debug &
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
    printf 'Flask server restarted inside container.\n'
    continue
  fi

  exit "$exit_code"
done
