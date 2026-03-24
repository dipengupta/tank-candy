from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AAA_STATE_AVERAGES_URL = "https://gasprices.aaa.com/state-gas-price-averages/"
EIA_REGULAR_XLS_URL = "https://www.eia.gov/petroleum/gasdiesel/xls/pswrgvwall.xls"
EIA_DIESEL_XLS_URL = "https://www.eia.gov/petroleum/gasdiesel/xls/psw18vwall.xls"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

REGULAR_SHEET_NAME = "Data 3"
DIESEL_SHEET_NAME = "Data 1"

REGULAR_HEADERS = {
    "east_coast": (
        "Weekly East Coast Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "new_england": (
        "Weekly New England (PADD 1A) Regular All Formulations Retail "
        "Gasoline Prices  (Dollars per Gallon)"
    ),
    "central_atlantic": (
        "Weekly Central Atlantic (PADD 1B) Regular All Formulations Retail "
        "Gasoline Prices  (Dollars per Gallon)"
    ),
    "lower_atlantic": (
        "Weekly Lower Atlantic (PADD 1C) Regular All Formulations Retail "
        "Gasoline Prices  (Dollars per Gallon)"
    ),
    "midwest": (
        "Weekly Midwest Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "gulf_coast": (
        "Weekly Gulf Coast Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "rocky_mountain": (
        "Weekly Rocky Mountain Regular All Formulations Retail Gasoline "
        "Prices  (Dollars per Gallon)"
    ),
    "west_coast": (
        "Weekly West Coast Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "california": (
        "Weekly California Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "colorado": (
        "Weekly Colorado Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "florida": (
        "Weekly Florida Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "massachusetts": (
        "Weekly Massachusetts Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "minnesota": (
        "Weekly Minnesota Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "new_york": (
        "Weekly New York Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "ohio": (
        "Weekly Ohio Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "texas": (
        "Weekly Texas Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
    "washington": (
        "Weekly Washington Regular All Formulations Retail Gasoline Prices  "
        "(Dollars per Gallon)"
    ),
}

DIESEL_HEADERS = {
    "east_coast": (
        "Weekly East Coast No 2 Diesel Retail Prices  (Dollars per Gallon)"
    ),
    "new_england": (
        "Weekly New England (PADD 1A) No 2 Diesel Retail Prices  "
        "(Dollars per Gallon)"
    ),
    "central_atlantic": (
        "Weekly Central Atlantic (PADD 1B) No 2 Diesel Retail Prices  "
        "(Dollars per Gallon)"
    ),
    "lower_atlantic": (
        "Weekly Lower Atlantic (PADD 1C) No 2 Diesel Retail Prices  "
        "(Dollars per Gallon)"
    ),
    "midwest": (
        "Weekly Midwest No 2 Diesel Retail Prices  (Dollars per Gallon)"
    ),
    "gulf_coast": (
        "Weekly Gulf Coast No 2 Diesel Retail Prices  (Dollars per Gallon)"
    ),
    "rocky_mountain": (
        "Weekly Rocky Mountain No 2 Diesel Retail Prices  (Dollars per Gallon)"
    ),
    "west_coast": (
        "Weekly West Coast No 2 Diesel Retail Prices  (Dollars per Gallon)"
    ),
    "california": (
        "Weekly California No 2 Diesel Retail Prices  (Dollars per Gallon)"
    ),
    "west_coast_ex_california": (
        "Weekly West Coast (PADD 5) Except California No 2 Diesel Retail "
        "Prices  (Dollars per Gallon)"
    ),
}

DIRECT_REGULAR_SERIES = {
    "CA": "california",
    "CO": "colorado",
    "FL": "florida",
    "MA": "massachusetts",
    "MN": "minnesota",
    "NY": "new_york",
    "OH": "ohio",
    "TX": "texas",
    "WA": "washington",
}

DIRECT_DIESEL_SERIES = {
    "CA": "california",
}


@dataclass(frozen=True)
class VehicleSpec:
    id: str
    name: str
    label: str
    tank_capacity: float
    fuel_type: str
    accent: str
    tagline: str
    silhouette: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label,
            "tankCapacity": self.tank_capacity,
            "fuelType": self.fuel_type,
            "accent": self.accent,
            "tagline": self.tagline,
            "silhouette": self.silhouette,
        }


VEHICLES = [
    VehicleSpec(
        id="hatchback",
        name="Hatchback",
        label="Compact hatch",
        tank_capacity=12.4,
        fuel_type="regular",
        accent="#ff6b57",
        tagline="City-sized and easy on the wallet.",
        silhouette="hatchback",
    ),
    VehicleSpec(
        id="coupe",
        name="Coupe",
        label="Sport coupe",
        tank_capacity=14.0,
        fuel_type="regular",
        accent="#ff8f3f",
        tagline="A little sleeker, a little thirstier.",
        silhouette="coupe",
    ),
    VehicleSpec(
        id="sedan",
        name="Sedan",
        label="Everyday sedan",
        tank_capacity=15.5,
        fuel_type="regular",
        accent="#f5b41b",
        tagline="The default all-rounder.",
        silhouette="sedan",
    ),
    VehicleSpec(
        id="wagon",
        name="Wagon",
        label="Family wagon",
        tank_capacity=16.4,
        fuel_type="regular",
        accent="#b7d63d",
        tagline="More cargo, still commuter-friendly.",
        silhouette="wagon",
    ),
    VehicleSpec(
        id="crossover",
        name="Crossover",
        label="Compact CUV",
        tank_capacity=16.8,
        fuel_type="regular",
        accent="#5ccc73",
        tagline="Tall ride height without going full SUV.",
        silhouette="crossover",
    ),
    VehicleSpec(
        id="minivan",
        name="Minivan",
        label="Minivan",
        tank_capacity=19.5,
        fuel_type="regular",
        accent="#16c2a3",
        tagline="Big family hauler, big fill-up.",
        silhouette="minivan",
    ),
    VehicleSpec(
        id="suv",
        name="SUV",
        label="Midsize SUV",
        tank_capacity=20.5,
        fuel_type="regular",
        accent="#1eb4ff",
        tagline="Popular, practical, and noticeably thirstier.",
        silhouette="suv",
    ),
    VehicleSpec(
        id="pickup",
        name="Pickup Truck",
        label="Pickup",
        tank_capacity=26.0,
        fuel_type="regular",
        accent="#6382ff",
        tagline="A large tank for long hauls and hardware runs.",
        silhouette="pickup",
    ),
    VehicleSpec(
        id="cargo_van",
        name="Cargo Van",
        label="Cargo van",
        tank_capacity=24.0,
        fuel_type="regular",
        accent="#8c6cff",
        tagline="Utility-first, with a tank to match.",
        silhouette="cargo_van",
    ),
    VehicleSpec(
        id="box_truck",
        name="Box Truck",
        label="Box truck",
        tank_capacity=33.0,
        fuel_type="diesel",
        accent="#b65cff",
        tagline="Commercial rig territory starts here.",
        silhouette="box_truck",
    ),
    VehicleSpec(
        id="semi",
        name="Semi Truck",
        label="Semi",
        tank_capacity=125.0,
        fuel_type="diesel",
        accent="#ff4fa4",
        tagline="Uses diesel, and the math gets serious fast.",
        silhouette="semi",
    ),
]


STATE_INFO = {
    "AK": {"name": "Alaska", "region": "west_coast", "tile": (0, 0)},
    "AL": {"name": "Alabama", "region": "gulf_coast", "tile": (5, 6)},
    "AR": {"name": "Arkansas", "region": "gulf_coast", "tile": (4, 4)},
    "AZ": {"name": "Arizona", "region": "west_coast", "tile": (4, 1)},
    "CA": {"name": "California", "region": "west_coast", "tile": (3, 1)},
    "CO": {"name": "Colorado", "region": "rocky_mountain", "tile": (3, 3)},
    "CT": {"name": "Connecticut", "region": "new_england", "tile": (3, 11)},
    "DC": {"name": "District of Columbia", "region": "central_atlantic", "tile": (4, 9)},
    "DE": {"name": "Delaware", "region": "central_atlantic", "tile": (4, 8)},
    "FL": {"name": "Florida", "region": "lower_atlantic", "tile": (6, 8)},
    "GA": {"name": "Georgia", "region": "lower_atlantic", "tile": (5, 7)},
    "HI": {"name": "Hawaii", "region": "west_coast", "tile": (6, 0)},
    "IA": {"name": "Iowa", "region": "midwest", "tile": (2, 5)},
    "ID": {"name": "Idaho", "region": "rocky_mountain", "tile": (1, 2)},
    "IL": {"name": "Illinois", "region": "midwest", "tile": (2, 6)},
    "IN": {"name": "Indiana", "region": "midwest", "tile": (2, 7)},
    "KS": {"name": "Kansas", "region": "midwest", "tile": (4, 3)},
    "KY": {"name": "Kentucky", "region": "midwest", "tile": (3, 6)},
    "LA": {"name": "Louisiana", "region": "gulf_coast", "tile": (5, 4)},
    "MA": {"name": "Massachusetts", "region": "new_england", "tile": (2, 11)},
    "MD": {"name": "Maryland", "region": "central_atlantic", "tile": (3, 9)},
    "ME": {"name": "Maine", "region": "new_england", "tile": (1, 11)},
    "MI": {"name": "Michigan", "region": "midwest", "tile": (1, 7)},
    "MN": {"name": "Minnesota", "region": "midwest", "tile": (1, 5)},
    "MO": {"name": "Missouri", "region": "midwest", "tile": (3, 5)},
    "MS": {"name": "Mississippi", "region": "gulf_coast", "tile": (5, 5)},
    "MT": {"name": "Montana", "region": "rocky_mountain", "tile": (1, 3)},
    "NC": {"name": "North Carolina", "region": "lower_atlantic", "tile": (4, 6)},
    "ND": {"name": "North Dakota", "region": "midwest", "tile": (1, 4)},
    "NE": {"name": "Nebraska", "region": "midwest", "tile": (3, 4)},
    "NH": {"name": "New Hampshire", "region": "new_england", "tile": (1, 10)},
    "NJ": {"name": "New Jersey", "region": "central_atlantic", "tile": (3, 10)},
    "NM": {"name": "New Mexico", "region": "gulf_coast", "tile": (4, 2)},
    "NV": {"name": "Nevada", "region": "west_coast", "tile": (2, 2)},
    "NY": {"name": "New York", "region": "central_atlantic", "tile": (2, 10)},
    "OH": {"name": "Ohio", "region": "midwest", "tile": (2, 8)},
    "OK": {"name": "Oklahoma", "region": "midwest", "tile": (5, 3)},
    "OR": {"name": "Oregon", "region": "west_coast", "tile": (2, 1)},
    "PA": {"name": "Pennsylvania", "region": "central_atlantic", "tile": (2, 9)},
    "RI": {"name": "Rhode Island", "region": "new_england", "tile": (3, 12)},
    "SC": {"name": "South Carolina", "region": "lower_atlantic", "tile": (4, 7)},
    "SD": {"name": "South Dakota", "region": "midwest", "tile": (2, 4)},
    "TN": {"name": "Tennessee", "region": "midwest", "tile": (4, 5)},
    "TX": {"name": "Texas", "region": "gulf_coast", "tile": (5, 2)},
    "UT": {"name": "Utah", "region": "rocky_mountain", "tile": (3, 2)},
    "VA": {"name": "Virginia", "region": "lower_atlantic", "tile": (3, 8)},
    "VT": {"name": "Vermont", "region": "new_england", "tile": (1, 9)},
    "WA": {"name": "Washington", "region": "west_coast", "tile": (1, 1)},
    "WI": {"name": "Wisconsin", "region": "midwest", "tile": (1, 6)},
    "WV": {"name": "West Virginia", "region": "lower_atlantic", "tile": (3, 7)},
    "WY": {"name": "Wyoming", "region": "rocky_mountain", "tile": (2, 3)},
}

STATE_NAME_TO_CODE = {info["name"]: code for code, info in STATE_INFO.items()}
VEHICLE_LOOKUP = {vehicle.id: vehicle for vehicle in VEHICLES}
