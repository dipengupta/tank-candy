# AGENTS.md

Instructions in this file apply to the entire repository.

## Project overview

- Tank Candy is a Flask single-page app that calculates vehicle fill-up costs from stored fuel data.
- The web app reads from SQLite only. Upstream AAA/EIA fetching happens outside the request path.
- Seed data lives at `data/seed_fuel_data.json` and is used to bootstrap a new database.
- The main user-facing surfaces are `/`, `GET /api/quote`, `GET /api/map`, and `GET /health`.

## Stack and important files

- Python 3 with Flask, requests, BeautifulSoup, APScheduler, and pytest.
- `app.py`: Flask app factory and HTTP routes.
- `fuel_service.py`: quote and map payload generation.
- `fuel_repository.py`: SQLite schema, bootstrap, and query layer.
- `fuel_sync.py`: upstream scraping/parsing logic.
- `fuel_jobs.py`: manual refresh and scheduler entrypoints.
- `templates/index.html`, `static/app.js`, `static/styles.css`: frontend UI.
- `tests/test_fuel_data.py`: main regression coverage.

## Working rules

- Preserve the architecture split: request handlers should not fetch AAA/EIA data directly.
- Keep all app reads going through the repository/service layers rather than ad hoc SQL in route handlers.
- Favor small, targeted changes over broad rewrites.
- Keep seed/bootstrap behavior working for a brand-new environment with no existing SQLite file.
- If you change quote selection, map output, source labels, fallback rules, or health behavior, update tests in `tests/test_fuel_data.py`.
- For sync-related tests, prefer fakes/stubs over live network access.
- Do not introduce new heavy infrastructure or services unless the task explicitly requires it.

## Local workflow

Preferred inner loop:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app:create_app run --debug
```

Useful commands:

```bash
python -m fuel_jobs refresh-now
python -m fuel_jobs run-scheduler
pytest -q
curl http://127.0.0.1:5000/health
docker compose up --build
```

## Validation

- After code changes, run `pytest -q`.
- If you changed app startup, routing, or persistence wiring, also verify `/health` locally.
- If you changed frontend behavior or API payload shape, verify the relevant browser flow manually or describe what could not be checked.
- Do not claim a refresh or scrape path works unless you actually exercised it or explicitly state that it was not run.
- After changes to the repo, read the existing docs and update them when the behavior, workflow, commands, architecture, or setup instructions have changed.

## Change guidance

- Match the existing style: straightforward Python, minimal abstraction, explicit tests.
- Keep JSON payload fields stable unless the task requires an API change.
- Prefer deterministic tests that build temporary repositories and seed data rather than relying on wall-clock state beyond `date.today()` patterns already used here.
- When changing Docker or startup scripts, preserve the current local/dev behavior unless the task explicitly changes it.
