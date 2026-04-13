#!/usr/bin/env sh

set -eu

RUN_SCHEDULER_INLINE="${RUN_SCHEDULER_INLINE:-1}"
scheduler_pid=""
web_pid=""

stop_child() {
  pid="$1"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
}

shutdown() {
  stop_child "$web_pid"
  stop_child "$scheduler_pid"
  exit 0
}

trap 'shutdown' INT TERM

if [ "$RUN_SCHEDULER_INLINE" = "1" ]; then
  python -m fuel_jobs run-scheduler &
  scheduler_pid=$!
fi

sh /app/start-web.sh &
web_pid=$!

while true; do
  if ! kill -0 "$web_pid" 2>/dev/null; then
    wait "$web_pid" || true
    stop_child "$scheduler_pid"
    exit 1
  fi

  if [ -n "$scheduler_pid" ] && ! kill -0 "$scheduler_pid" 2>/dev/null; then
    wait "$scheduler_pid" || true
    stop_child "$web_pid"
    exit 1
  fi

  sleep 1
done
