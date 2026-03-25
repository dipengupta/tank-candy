#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${FLASK_HOST:-127.0.0.1}"
PORT="${FLASK_PORT:-5000}"
DOCKER_URL="${DOCKER_URL:-http://127.0.0.1:5001}"

cd "$ROOT_DIR"

# Bash 3.2 on macOS does not support associative arrays.
# Track seen PIDs in a newline-delimited string instead.
SEEN_PIDS=$'\n'

docker_compose_available() {
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

docker_web_running() {
  local container_id
  container_id="$(docker compose ps -q web 2>/dev/null || true)"
  [[ -n "$container_id" ]]
}

docker_web_uses_restartable_supervisor() {
  local pid_one
  pid_one="$(docker compose exec -T web sh -lc 'ps -o args= 1' 2>/dev/null || true)"
  [[ "$pid_one" == *"container-web.sh"* ]]
}

restart_docker_web() {
  if ! docker_web_uses_restartable_supervisor; then
    printf '%s\n' \
      "The running web container is still using the old startup command." \
      "Run 'docker compose up -d --build web' once, then use ./restart.sh for in-place restarts." >&2
    exit 1
  fi

  docker compose kill -s USR1 web >/dev/null
  printf 'Docker web server restarted.\n'
  printf 'URL: %s\n' "$DOCKER_URL"
  exit 0
}

find_flask_bin() {
  if [[ -x "$ROOT_DIR/.venv/bin/flask" ]]; then
    printf '%s\n' "$ROOT_DIR/.venv/bin/flask"
    return 0
  fi

  if command -v flask >/dev/null 2>&1; then
    command -v flask
    return 0
  fi

  printf 'Unable to find a Flask executable. Create .venv or install flask in PATH.\n' >&2
  exit 1
}

stop_pid() {
  local pid="$1"

  if ! kill -0 "$pid" >/dev/null 2>&1; then
    return 0
  fi

  kill "$pid" >/dev/null 2>&1 || true

  for _ in {1..20}; do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done

  kill -9 "$pid" >/dev/null 2>&1 || true
}

remember_pid() {
  local pid="$1"

  [[ "$pid" =~ ^[0-9]+$ ]] || return 0

  case "$SEEN_PIDS" in
    *$'\n'"$pid"$'\n'*)
      return 0
      ;;
  esac

  SEEN_PIDS+="$pid"$'\n'
  printf '%s\n' "$pid"
}

find_existing_pids() {
  if command -v ps >/dev/null 2>&1; then
    while read -r pid cmdline; do
      if [[ "$cmdline" == *"flask --app app run --debug --host "* && "$cmdline" == *" --port $PORT"* ]]; then
        remember_pid "$pid"
      fi
      if [[ "$cmdline" == *"flask --app app:create_app run --debug --host "* && "$cmdline" == *" --port $PORT"* ]]; then
        remember_pid "$pid"
      fi
    done < <(ps -eo pid=,args=)
  fi

  if command -v lsof >/dev/null 2>&1; then
    while IFS= read -r pid; do
      remember_pid "$pid"
    done < <(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
  fi
}

if docker_compose_available && docker_web_running; then
  restart_docker_web
fi

while IFS= read -r pid; do
  stop_pid "$pid"
done < <(find_existing_pids)

FLASK_BIN="$(find_flask_bin)"

nohup "$FLASK_BIN" --app app:create_app run --debug --host "$HOST" --port "$PORT" >/dev/null 2>&1 &
server_pid=$!

printf 'Server restarted.\n'
printf 'PID: %s\n' "$server_pid"
printf 'URL: http://%s:%s\n' "$HOST" "$PORT"
