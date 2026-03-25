from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from fuel_repository import FuelRepository
from fuel_service import FuelDataService
from fuel_sync import FuelSyncService


def build_repository(tmp_path: Path) -> FuelRepository:
    return FuelRepository(tmp_path / "fuel_prices.db")


def test_bootstrap_from_seed_loads_initial_data(tmp_path: Path) -> None:
    repository = build_repository(tmp_path)
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "daily_snapshots": [
                    {
                        "snapshot_date": "2026-03-24",
                        "states": {
                            "PA": {
                                "regular": 3.95,
                                "mid_grade": 4.35,
                                "premium": 4.7,
                                "diesel": 4.8,
                            }
                        },
                    }
                ],
                "history": {
                    "regular": {
                        "latest_date": "2026-03-23",
                        "series": {
                            "central_atlantic": [["2026-03-23", 3.8]],
                        },
                    },
                    "diesel": {
                        "latest_date": "2026-03-23",
                        "series": {
                            "gulf_coast": [["2026-03-23", 3.4]],
                        },
                    },
                },
            }
        )
    )

    assert repository.bootstrap_from_seed(seed_path) is True
    assert repository.get_daily_snapshot("2026-03-24", "PA")["regular"] == 3.95
    assert (
        repository.get_history_value("regular", "central_atlantic", "2026-03-23") == 3.8
    )


def test_service_uses_exact_stored_daily_snapshot(tmp_path: Path) -> None:
    today = date.today().isoformat()
    repository = build_repository(tmp_path)
    repository.upsert_daily_snapshot(
        today,
        {
            "PA": {
                "regular": 3.95,
                "mid_grade": 4.35,
                "premium": 4.7,
                "diesel": 4.8,
            }
        },
    )

    service = FuelDataService(repository)
    quote = service.get_quote("PA", today, "sedan")

    assert quote["pricePerGallon"] == 3.95
    assert quote["startingFuelLevel"] == 0.10
    assert quote["fillShare"] == 0.90
    assert quote["gallonsToFill"] == 13.95
    assert quote["totalCost"] == 55.1
    assert quote["source"]["label"] == "Stored AAA daily state snapshot"
    assert quote["isEstimated"] is False


def test_service_supports_motorcycle_vehicle_types(tmp_path: Path) -> None:
    today = date.today().isoformat()
    repository = build_repository(tmp_path)
    repository.upsert_daily_snapshot(
        today,
        {
            "PA": {
                "regular": 4.0,
                "mid_grade": 4.35,
                "premium": 4.7,
                "diesel": 4.8,
            }
        },
    )

    service = FuelDataService(repository)
    quote = service.get_quote("PA", today, "touring_bike")

    assert quote["vehicle"]["name"] == "Touring Bike"
    assert quote["tankCapacityGallons"] == 6.1
    assert quote["fuelType"] == "regular"
    assert quote["gallonsToFill"] == 5.49
    assert quote["totalCost"] == 21.96


def test_service_falls_back_to_latest_stored_snapshot_for_today(tmp_path: Path) -> None:
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    repository = build_repository(tmp_path)
    repository.upsert_daily_snapshot(
        yesterday,
        {
            "PA": {
                "regular": 3.91,
                "mid_grade": 4.31,
                "premium": 4.65,
                "diesel": 4.75,
            }
        },
    )

    service = FuelDataService(repository)
    quote = service.get_quote("PA", today.isoformat(), "sedan")

    assert quote["pricePerGallon"] == 3.91
    assert quote["totalCost"] == 54.54
    assert quote["source"]["label"] == "Latest stored AAA state snapshot"
    assert quote["isEstimated"] is False


def test_service_estimates_history_from_region_when_no_direct_state_series(tmp_path: Path) -> None:
    today = date.today().isoformat()
    repository = build_repository(tmp_path)
    repository.upsert_daily_snapshot(
        today,
        {
            "PA": {
                "regular": 4.0,
                "mid_grade": 4.4,
                "premium": 4.8,
                "diesel": 4.9,
            }
        },
    )
    repository.replace_history(
        "regular",
        latest_date=today,
        series={
            "central_atlantic": {
                "dates": ["2026-01-19", today],
                "values": [3.0, 3.5],
            }
        },
    )

    service = FuelDataService(repository)
    quote = service.get_quote("PA", "2026-01-24", "sedan")

    assert quote["isEstimated"] is True
    assert quote["effectiveDate"] == "2026-01-19"
    assert quote["pricePerGallon"] == round(3.0 * (4.0 / 3.5), 3)


def test_service_uses_direct_state_history_when_available(tmp_path: Path) -> None:
    repository = build_repository(tmp_path)
    repository.replace_history(
        "regular",
        latest_date="2026-03-24",
        series={
            "california": {
                "dates": ["2026-01-19"],
                "values": [3.99],
            }
        },
    )

    service = FuelDataService(repository)
    quote = service.get_quote("CA", "2026-01-24", "sedan")

    assert quote["isEstimated"] is False
    assert quote["pricePerGallon"] == 3.99
    assert quote["source"]["label"] == "Stored EIA weekly state series"


class FakeSourceClient:
    def fetch_current_state_prices(self):
        return {
            "as_of": "2026-03-24",
            "states": {
                "PA": {
                    "regular": 3.95,
                    "mid_grade": 4.35,
                    "premium": 4.7,
                    "diesel": 4.8,
                }
            },
        }

    def fetch_regular_history(self):
        return {
            "latest_date": "2026-03-23",
            "series": {
                "central_atlantic": {
                    "dates": ["2026-03-23"],
                    "values": [3.8],
                }
            },
        }

    def fetch_diesel_history(self):
        return {
            "latest_date": "2026-03-23",
            "series": {
                "gulf_coast": {
                    "dates": ["2026-03-23"],
                    "values": [3.4],
                }
            },
        }


def test_sync_service_persists_source_payloads(tmp_path: Path) -> None:
    repository = build_repository(tmp_path)
    sync_service = FuelSyncService(repository, FakeSourceClient())

    result = sync_service.refresh_all()

    assert result["current"]["rows"] == 1
    assert repository.get_daily_snapshot("2026-03-24", "PA")["regular"] == 3.95
    assert repository.get_history_value("regular", "central_atlantic", "2026-03-23") == 3.8
