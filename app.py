from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, current_app, jsonify, render_template, request

from fuel_repository import FuelRepository
from fuel_service import FuelDataError, FuelDataService


def format_display_date(value: str) -> str:
    return date.fromisoformat(value).strftime("%b %d, %Y").replace(" 0", " ")


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        JSON_SORT_KEYS=False,
        DATABASE_PATH=Path(os.getenv("DATABASE_PATH", "data/fuel_prices.db")),
        SEED_DATA_PATH=Path(os.getenv("SEED_DATA_PATH", "data/seed_fuel_data.json")),
    )
    if test_config:
        app.config.update(test_config)

    fuel_repository = FuelRepository(Path(app.config["DATABASE_PATH"]))
    fuel_repository.bootstrap_from_seed(Path(app.config["SEED_DATA_PATH"]))
    fuel_service = FuelDataService(fuel_repository)

    app.extensions["fuel_repository"] = fuel_repository
    app.extensions["fuel_service"] = fuel_service

    @app.route("/")
    def index():
        default_date = date.today().isoformat()
        default_state = "PA"
        default_vehicle = "sedan"
        vehicles = fuel_service.get_vehicle_catalog()
        states = fuel_service.get_states_payload()
        vehicle_lookup = {item["id"]: item for item in vehicles}
        state_lookup = {item["code"]: item for item in states}

        bootstrap = {
            "vehicles": vehicles,
            "states": states,
            "defaults": {
                "date": default_date,
                "state": default_state,
                "vehicle": default_vehicle,
                "minDate": "1990-08-20",
                "maxDate": default_date,
            },
            "sources": fuel_service.get_source_catalog(),
            "ui": {
                "defaultDateLabel": format_display_date(default_date),
                "defaultDateCaption": "Today",
                "minDateLabel": format_display_date("1990-08-20"),
                "maxDateLabel": format_display_date(default_date),
                "defaultVehicleName": vehicle_lookup[default_vehicle]["name"],
                "defaultTankCapacityLabel": (
                    f"{vehicle_lookup[default_vehicle]['tankCapacity']:.1f} gal"
                ),
                "defaultFuelTypeLabel": vehicle_lookup[default_vehicle][
                    "fuelType"
                ].title(),
                "defaultStateName": state_lookup[default_state]["name"],
            },
        }
        return render_template("index.html", bootstrap=bootstrap)

    @app.get("/api/quote")
    def get_quote():
        state_code = request.args.get("state", "PA")
        selected_date = request.args.get("date", date.today().isoformat())
        vehicle_id = request.args.get("vehicle", "sedan")

        try:
            payload = fuel_service.get_quote(
                state_code=state_code,
                selected_date=selected_date,
                vehicle_id=vehicle_id,
            )
        except FuelDataError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            current_app.logger.exception("Quote request failed")
            return (
                jsonify(
                    {
                        "error": (
                            "Fuel data is temporarily unavailable. "
                            "Please retry in a moment."
                        )
                    }
                ),
                502,
            )

        return jsonify(payload)

    @app.get("/api/map")
    def get_map_snapshot():
        selected_date = request.args.get("date", date.today().isoformat())
        vehicle_id = request.args.get("vehicle", "sedan")

        try:
            payload = fuel_service.get_map_snapshot(
                selected_date=selected_date,
                vehicle_id=vehicle_id,
            )
        except FuelDataError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            current_app.logger.exception("Map snapshot request failed")
            return (
                jsonify(
                    {
                        "error": (
                            "Fuel map data is temporarily unavailable. "
                            "Please retry in a moment."
                        )
                    }
                ),
                502,
            )

        return jsonify(payload)

    @app.get("/health")
    def health():
        try:
            return jsonify(fuel_repository.get_health_snapshot())
        except Exception:
            current_app.logger.exception("Health check failed")
            return jsonify({"status": "error"}), 503

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
