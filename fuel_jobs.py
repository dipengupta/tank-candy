from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from fuel_repository import FuelRepository
from fuel_sync import FuelSourceClient, FuelSyncService


DEFAULT_DB_PATH = Path(os.getenv("DATABASE_PATH", "data/fuel_prices.db"))
DEFAULT_SEED_PATH = Path(os.getenv("SEED_DATA_PATH", "data/seed_fuel_data.json"))


def build_repository() -> FuelRepository:
    repository = FuelRepository(DEFAULT_DB_PATH)
    repository.bootstrap_from_seed(DEFAULT_SEED_PATH)
    return repository


def refresh_now() -> dict[str, object]:
    repository = build_repository()
    sync_service = FuelSyncService(repository, FuelSourceClient())
    result = sync_service.refresh_all()
    print(json.dumps(result, indent=2))
    return result


def run_scheduler() -> None:
    repository = build_repository()
    sync_service = FuelSyncService(repository, FuelSourceClient())

    try:
        result = sync_service.refresh_all()
        print(json.dumps({"initial_refresh": result}, indent=2))
    except Exception as exc:
        print(json.dumps({"initial_refresh_error": str(exc)}, indent=2))

    scheduler = BlockingScheduler(timezone=os.getenv("APP_TIMEZONE", "America/New_York"))
    scheduler.add_job(
        sync_service.refresh_current_prices,
        "cron",
        id="daily_state_prices",
        hour="6,18",
        minute="5",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_service.refresh_histories,
        "cron",
        id="fuel_histories",
        hour="7",
        minute="0",
        replace_existing=True,
    )
    scheduler.start()


def build_seed(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = FuelSourceClient()
    current = client.fetch_current_state_prices()
    regular = client.fetch_regular_history()
    diesel = client.fetch_diesel_history()
    payload = {
        "metadata": {"seed_built_at": current["as_of"]},
        "daily_snapshots": [
            {
                "snapshot_date": current["as_of"],
                "states": current["states"],
            }
        ],
        "history": {
            "regular": regular,
            "diesel": diesel,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2))
    print(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fuel data jobs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("refresh-now")
    subparsers.add_parser("run-scheduler")

    build_seed_parser = subparsers.add_parser("build-seed")
    build_seed_parser.add_argument(
        "--output",
        default=str(DEFAULT_SEED_PATH),
        help="Path to write the bundled seed JSON file.",
    )

    args = parser.parse_args()

    if args.command == "refresh-now":
        refresh_now()
        return
    if args.command == "run-scheduler":
        run_scheduler()
        return
    if args.command == "build-seed":
        build_seed(Path(args.output))
        return


if __name__ == "__main__":
    main()
