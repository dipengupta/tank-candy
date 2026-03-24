# Tank Candy

Single-page Flask app for visualizing what it costs to fill different vehicles from empty across U.S. states and dates.

## Architecture

- The web app reads fuel data from SQLite only.
- A separate scheduler process refreshes upstream data on a schedule.
- The app ships with a bundled seed dataset at `data/seed_fuel_data.json`, so a brand-new machine still has data to display before the first scheduled refresh runs.

## Data flow

### 1. Upstream fetch

- AAA current state averages are scraped from the AAA state averages page and parsed into one daily snapshot per state.
- EIA gasoline and diesel history are downloaded as Excel workbooks and parsed into weekly time-series rows.
- The source-fetching and parsing code lives in `fuel_sync.py`.

### 2. Refresh and update

- Refreshing happens outside the Flask web request path.
- `python -m fuel_jobs refresh-now` performs an immediate sync of AAA daily data plus both EIA history datasets.
- `python -m fuel_jobs run-scheduler` performs an initial refresh, then keeps data updated on a schedule.
- Default schedule:
  - AAA daily state snapshots at 6:05 AM and 6:05 PM America/New_York
  - EIA history refresh at 7:00 AM America/New_York
- The scheduler and CLI entrypoints live in `fuel_jobs.py`.

### 3. Storage

- All app reads go through SQLite at `data/fuel_prices.db`.
- The main tables are:
  - `daily_state_prices`: one row per `snapshot_date + state_code`
  - `fuel_history`: one row per `fuel_type + series_key + week_start`
  - `metadata`: latest refresh markers and seed metadata
- A brand-new environment can bootstrap the database from `data/seed_fuel_data.json` before any scheduled refresh has run.
- SQLite schema and queries live in `fuel_repository.py`.

### 4. Quote resolution

- The browser never calls AAA or EIA directly.
- The browser calls `GET /api/quote`, and Flask delegates quote building to `FuelDataService` in `fuel_service.py`.
- Quote selection logic is:
  1. Use an exact stored AAA daily snapshot when the requested state/date exists.
  2. If the user asked for today and an older stored AAA snapshot exists on or before today, use that latest stored daily snapshot.
  3. Otherwise use the stored EIA weekly history for the matching state series.
  4. If no direct state EIA series exists, estimate from the matching EIA regional series and calibrate using the latest stored AAA state-vs-region spread.
  5. If no historical series is available, fall back to the latest stored AAA snapshot.

### 5. Display in the UI

- `app.py` serves the initial page bootstrap with vehicle, state, and date defaults.
- The frontend in `static/app.js` calls `/api/quote` when the user changes vehicle, state, or date.
- The API response includes:
  - requested date and effective date
  - selected state and vehicle
  - fuel type and tank capacity
  - `pricePerGallon` and `totalCost`
  - source metadata, explanatory note, and whether the value is estimated
- The frontend renders those values into the hero totals, source section, tank bar, and the "vs today" comparison card.

### Operational note

- If the scheduler is not running and `refresh-now` has not been executed recently, the app will show whatever is already stored in SQLite or bundled in the seed file.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m fuel_jobs refresh-now
flask --app app run --debug
```

Open `http://127.0.0.1:5000`.

To restart the Flask dev server later without retyping the command:

```bash
./restart.sh
```

The helper stops the existing Flask dev server by matching the current app process and listening port, then starts it again in the background without writing PID or log files.

## Scheduler

Run the separate refresh worker:

```bash
source .venv/bin/activate
python -m fuel_jobs run-scheduler
```

Default schedule:

- AAA daily state snapshots: 6:05 AM and 6:05 PM America/New_York
- EIA history refresh: 7:00 AM America/New_York

## Tests

```bash
source .venv/bin/activate
pytest -q
```

## Docker

Build the image:

```bash
docker build -t gas-price-project:test .
```

Run both the web app and scheduler:

```bash
docker compose up --build
```

Services:

- `web`: Flask dev server on port `5000`
- `scheduler`: separate process that refreshes stored data into the shared SQLite volume

## Important files

- `app.py`: Flask entrypoint
- `fuel_service.py`: quote generation from stored data
- `fuel_repository.py`: SQLite schema and queries
- `fuel_sync.py`: source scraping/parsing and persistence
- `fuel_jobs.py`: refresh CLI and scheduler entrypoint
- `data/seed_fuel_data.json`: bundled fallback data

## Sources

- AAA Fuel Prices: <https://gasprices.aaa.com/state-gas-price-averages/>
- EIA Gasoline and Diesel Fuel Update: <https://www.eia.gov/petroleum/gasdiesel/>
