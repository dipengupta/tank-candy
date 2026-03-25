from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


workers = env_int("WEB_CONCURRENCY", 1)
threads = env_int("GUNICORN_THREADS", 4)
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
timeout = env_int("GUNICORN_TIMEOUT", 30)
graceful_timeout = env_int("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = env_int("GUNICORN_KEEPALIVE", 5)
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
capture_output = True
preload_app = True
