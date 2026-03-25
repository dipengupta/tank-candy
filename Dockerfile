FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/runtime-data/fuel_prices.db
ENV SEED_DATA_PATH=/app/data/seed_fuel_data.json
ENV PORT=5000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/runtime-data \
    && chmod +x /app/start-web.sh /app/container-web.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.getenv('PORT', '5000')}/health\", timeout=3).read()"]

CMD ["sh", "/app/start-web.sh"]
