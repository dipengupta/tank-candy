from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from fuel_domain import (
    AAA_STATE_AVERAGES_URL,
    DIRECT_DIESEL_SERIES,
    DIRECT_REGULAR_SERIES,
    STATE_INFO,
    VEHICLES,
    VEHICLE_LOOKUP,
)
from fuel_repository import FuelRepository


class FuelDataError(ValueError):
    pass


@dataclass(frozen=True)
class QuoteSource:
    label: str
    detail: str
    links: list[dict[str, str]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "detail": self.detail,
            "links": self.links,
        }


class FuelDataService:
    def __init__(self, repository: FuelRepository):
        self.repository = repository

    def get_vehicle_catalog(self) -> list[dict[str, Any]]:
        return [vehicle.as_dict() for vehicle in VEHICLES]

    def get_states_payload(self) -> list[dict[str, Any]]:
        payload = []
        for code, info in STATE_INFO.items():
            row, col = info["tile"]
            payload.append(
                {
                    "code": code,
                    "name": info["name"],
                    "region": info["region"],
                    "tileRow": row,
                    "tileColumn": col,
                }
            )
        return sorted(payload, key=lambda item: item["name"])

    def get_source_catalog(self) -> list[dict[str, str]]:
        return [
            {"label": "AAA Fuel Prices", "url": AAA_STATE_AVERAGES_URL},
            {
                "label": "EIA Gasoline and Diesel Fuel Update",
                "url": "https://www.eia.gov/petroleum/gasdiesel/",
            },
        ]

    def get_quote(
        self, state_code: str, selected_date: str, vehicle_id: str
    ) -> dict[str, Any]:
        state_code = state_code.upper().strip()
        if state_code not in STATE_INFO:
            raise FuelDataError("Select a valid U.S. state or DC.")

        try:
            requested_date = date.fromisoformat(selected_date)
        except ValueError as exc:
            raise FuelDataError("Select a valid date.") from exc

        if requested_date > date.today():
            raise FuelDataError("Future fuel prices are not available.")

        vehicle = VEHICLE_LOOKUP.get(vehicle_id)
        if vehicle is None:
            raise FuelDataError("Select a valid vehicle type.")

        fuel_type = vehicle.fuel_type
        min_supported = date(1990, 8, 20) if fuel_type == "regular" else date(1994, 3, 21)
        if requested_date < min_supported:
            raise FuelDataError(
                f"{fuel_type.title()} history in this app starts on {min_supported.isoformat()}."
            )

        price_info = self._resolve_price(
            state_code=state_code,
            requested_date=requested_date,
            fuel_type=fuel_type,
        )
        total_cost = round(price_info["price_per_gallon"] * vehicle.tank_capacity, 2)

        return {
            "requestedDate": requested_date.isoformat(),
            "effectiveDate": price_info["effective_date"],
            "requestedState": {
                "code": state_code,
                "name": STATE_INFO[state_code]["name"],
            },
            "vehicle": vehicle.as_dict(),
            "fuelType": vehicle.fuel_type,
            "tankCapacityGallons": vehicle.tank_capacity,
            "pricePerGallon": price_info["price_per_gallon"],
            "totalCost": total_cost,
            "headline": self._build_headline(vehicle.name, vehicle.fuel_type, state_code, total_cost),
            "source": price_info["source"].as_dict(),
            "dateNote": price_info["date_note"],
            "isEstimated": price_info["is_estimated"],
        }

    def _resolve_price(
        self, state_code: str, requested_date: date, fuel_type: str
    ) -> dict[str, Any]:
        exact_daily = self.repository.get_daily_snapshot(requested_date.isoformat(), state_code)
        if exact_daily is not None:
            return self._build_daily_result(
                state_code=state_code,
                snapshot=exact_daily,
                fuel_type=fuel_type,
                label="Stored AAA daily state snapshot",
                note=f"Exact stored AAA state snapshot for {exact_daily['snapshot_date']}.",
            )

        latest_snapshot = self.repository.get_latest_snapshot_on_or_before(
            requested_date.isoformat(), state_code
        )
        if requested_date == date.today() and latest_snapshot is not None:
            note = (
                f"Using the latest stored AAA state snapshot from "
                f"{latest_snapshot['snapshot_date']}."
            )
            return self._build_daily_result(
                state_code=state_code,
                snapshot=latest_snapshot,
                fuel_type=fuel_type,
                label="Latest stored AAA state snapshot",
                note=note,
            )

        return self._build_history_result(
            state_code=state_code,
            requested_date=requested_date,
            fuel_type=fuel_type,
        )

    def _build_daily_result(
        self,
        state_code: str,
        snapshot: dict[str, Any],
        fuel_type: str,
        label: str,
        note: str,
    ) -> dict[str, Any]:
        price_key = "diesel" if fuel_type == "diesel" else "regular"
        source = QuoteSource(
            label=label,
            detail=(
                f"Exact {STATE_INFO[state_code]['name']} {price_key} value stored from "
                "the AAA state averages page."
            ),
            links=[{"label": "AAA Fuel Prices", "url": AAA_STATE_AVERAGES_URL}],
        )
        return {
            "price_per_gallon": round(float(snapshot[price_key]), 3),
            "effective_date": snapshot["snapshot_date"],
            "date_note": note,
            "is_estimated": False,
            "source": source,
        }

    def _build_history_result(
        self, state_code: str, requested_date: date, fuel_type: str
    ) -> dict[str, Any]:
        target_week = requested_date - timedelta(days=requested_date.weekday())
        target_week_iso = target_week.isoformat()
        direct_series = (
            DIRECT_REGULAR_SERIES.get(state_code)
            if fuel_type == "regular"
            else DIRECT_DIESEL_SERIES.get(state_code)
        )
        region_key = STATE_INFO[state_code]["region"]
        region_series_key = (
            "west_coast_ex_california"
            if fuel_type == "diesel" and region_key == "west_coast" and state_code != "CA"
            else region_key
        )

        exact_price = None
        if direct_series:
            exact_price = self.repository.get_history_value(
                fuel_type=fuel_type,
                series_key=direct_series,
                target_week=target_week_iso,
            )

        if exact_price is not None:
            source = QuoteSource(
                label="Stored EIA weekly state series",
                detail=(
                    f"Exact weekly {STATE_INFO[state_code]['name']} {fuel_type} series "
                    "stored from EIA."
                ),
                links=[
                    {
                        "label": "EIA Gasoline and Diesel Fuel Update",
                        "url": "https://www.eia.gov/petroleum/gasdiesel/",
                    }
                ],
            )
            return {
                "price_per_gallon": round(exact_price, 3),
                "effective_date": target_week_iso,
                "date_note": self._weekly_note(requested_date, target_week),
                "is_estimated": False,
                "source": source,
            }

        region_price = self.repository.get_history_value(
            fuel_type=fuel_type,
            series_key=region_series_key,
            target_week=target_week_iso,
        )
        if region_price is None:
            fallback = self.repository.get_latest_snapshot(state_code)
            if fallback is None:
                raise FuelDataError("No stored fuel data is available yet.")
            return self._build_daily_result(
                state_code=state_code,
                snapshot=fallback,
                fuel_type=fuel_type,
                label="Latest stored fallback snapshot",
                note=(
                    f"Historical series unavailable; showing the latest stored AAA snapshot "
                    f"from {fallback['snapshot_date']}."
                ),
            )

        estimate = round(
            region_price
            * self._estimate_state_multiplier(
                state_code=state_code,
                fuel_type=fuel_type,
                region_series_key=region_series_key,
            ),
            3,
        )

        source = QuoteSource(
            label="Stored EIA weekly regional estimate",
            detail=(
                f"Estimated from the stored EIA {self._humanize_region(region_key)} weekly "
                "series, calibrated to the latest stored AAA state-vs-region spread."
            ),
            links=[
                {"label": "AAA Fuel Prices", "url": AAA_STATE_AVERAGES_URL},
                {
                    "label": "EIA Gasoline and Diesel Fuel Update",
                    "url": "https://www.eia.gov/petroleum/gasdiesel/",
                },
            ],
        )
        return {
            "price_per_gallon": estimate,
            "effective_date": target_week_iso,
            "date_note": self._weekly_note(requested_date, target_week),
            "is_estimated": True,
            "source": source,
        }

    def _estimate_state_multiplier(
        self, state_code: str, fuel_type: str, region_series_key: str
    ) -> float:
        latest_snapshot = self.repository.get_latest_snapshot(state_code)
        if latest_snapshot is None:
            return 1.0

        region_value = self.repository.get_history_value(
            fuel_type=fuel_type,
            series_key=region_series_key,
            target_week=latest_snapshot["snapshot_date"],
        )
        if not region_value or region_value <= 0:
            return 1.0

        state_value = latest_snapshot["diesel"] if fuel_type == "diesel" else latest_snapshot["regular"]
        multiplier = float(state_value) / region_value
        return max(0.72, min(1.35, multiplier))

    @staticmethod
    def _build_headline(
        vehicle_name: str, fuel_type: str, state_code: str, total_cost: float
    ) -> str:
        label = "fill-up" if fuel_type == "regular" else "diesel fill-up"
        state_name = STATE_INFO[state_code]["name"]
        return f"A full {vehicle_name.lower()} {label} in {state_name} is about ${total_cost:,.2f}."

    @staticmethod
    def _weekly_note(requested_date: date, target_week: date) -> str:
        if requested_date == target_week:
            return f"Historical requests use the stored EIA week of {target_week.isoformat()}."
        return (
            f"Historical dates use stored weekly EIA data, so {requested_date.isoformat()} "
            f"uses the week of {target_week.isoformat()}."
        )

    @staticmethod
    def _humanize_region(region_key: str) -> str:
        names = {
            "new_england": "New England",
            "central_atlantic": "Central Atlantic",
            "lower_atlantic": "Lower Atlantic",
            "midwest": "Midwest",
            "gulf_coast": "Gulf Coast",
            "rocky_mountain": "Rocky Mountain",
            "west_coast": "West Coast",
        }
        return names.get(region_key, region_key.replace("_", " ").title())
