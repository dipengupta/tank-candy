from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

import requests
import xlrd
from bs4 import BeautifulSoup

from fuel_domain import (
    AAA_STATE_AVERAGES_URL,
    DIESEL_HEADERS,
    DIESEL_SHEET_NAME,
    EIA_DIESEL_XLS_URL,
    EIA_REGULAR_XLS_URL,
    REGULAR_HEADERS,
    REGULAR_SHEET_NAME,
    REQUEST_HEADERS,
    STATE_NAME_TO_CODE,
)
from fuel_repository import FuelRepository


class FuelSyncError(RuntimeError):
    pass


class FuelSourceClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def fetch_current_state_prices(self) -> dict[str, Any]:
        response = self.session.get(
            AAA_STATE_AVERAGES_URL,
            headers=REQUEST_HEADERS,
            timeout=25,
        )
        response.raise_for_status()
        return self._parse_aaa_state_page(response.text)

    def fetch_regular_history(self) -> dict[str, Any]:
        return self._fetch_eia_history(
            url=EIA_REGULAR_XLS_URL,
            sheet_name=REGULAR_SHEET_NAME,
            headers=REGULAR_HEADERS,
        )

    def fetch_diesel_history(self) -> dict[str, Any]:
        return self._fetch_eia_history(
            url=EIA_DIESEL_XLS_URL,
            sheet_name=DIESEL_SHEET_NAME,
            headers=DIESEL_HEADERS,
        )

    def _fetch_eia_history(
        self, url: str, sheet_name: str, headers: dict[str, str]
    ) -> dict[str, Any]:
        response = self.session.get(url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
        workbook = xlrd.open_workbook(file_contents=response.content)
        return self._parse_eia_sheet(workbook, sheet_name, headers)

    def _parse_aaa_state_page(self, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table")
        if table is None:
            raise FuelSyncError("AAA state table could not be parsed.")

        date_match = re.search(r"Price as of (\d{1,2}/\d{1,2}/\d{2})", html)
        if not date_match:
            raise FuelSyncError("AAA pricing date could not be parsed.")

        as_of = datetime.strptime(date_match.group(1), "%m/%d/%y").date().isoformat()
        states: dict[str, dict[str, float]] = {}

        for row in table.select("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) < 5:
                continue

            code = STATE_NAME_TO_CODE.get(cells[0])
            if not code:
                continue

            states[code] = {
                "regular": self._money_to_float(cells[1]),
                "mid_grade": self._money_to_float(cells[2]),
                "premium": self._money_to_float(cells[3]),
                "diesel": self._money_to_float(cells[4]),
            }

        if not states:
            raise FuelSyncError("AAA state rows could not be parsed.")

        return {"as_of": as_of, "states": states}

    def _parse_eia_sheet(
        self, workbook: xlrd.book.Book, sheet_name: str, headers: dict[str, str]
    ) -> dict[str, Any]:
        sheet = workbook.sheet_by_name(sheet_name)
        header_row = sheet.row_values(2)

        indexes: dict[str, int] = {}
        for key, label in headers.items():
            try:
                indexes[key] = header_row.index(label)
            except ValueError as exc:
                raise FuelSyncError(f"EIA series header missing for {key}.") from exc

        series = {key: {"dates": [], "values": []} for key in headers}

        for rowx in range(3, sheet.nrows):
            raw_date = sheet.cell_value(rowx, 0)
            if raw_date in ("", None):
                continue

            week_start = xlrd.xldate_as_datetime(
                raw_date, workbook.datemode
            ).date().isoformat()

            for key, column_index in indexes.items():
                value = sheet.cell_value(rowx, column_index)
                if value in ("", None):
                    continue
                if isinstance(value, float) and math.isnan(value):
                    continue
                series[key]["dates"].append(week_start)
                series[key]["values"].append(float(value))

        latest_date = max(series[next(iter(series))]["dates"])
        return {"latest_date": latest_date, "series": series}

    @staticmethod
    def _money_to_float(value: str) -> float:
        return float(value.replace("$", "").replace(",", "").strip())


class FuelSyncService:
    def __init__(self, repository: FuelRepository, source_client: FuelSourceClient):
        self.repository = repository
        self.source_client = source_client

    def refresh_current_prices(self) -> dict[str, Any]:
        payload = self.source_client.fetch_current_state_prices()
        row_count = self.repository.upsert_daily_snapshot(
            snapshot_date=payload["as_of"],
            states=payload["states"],
        )
        return {
            "dataset": "daily_state_prices",
            "snapshot_date": payload["as_of"],
            "rows": row_count,
        }

    def refresh_histories(self) -> list[dict[str, Any]]:
        regular = self.source_client.fetch_regular_history()
        diesel = self.source_client.fetch_diesel_history()

        regular_rows = self.repository.replace_history(
            fuel_type="regular",
            latest_date=regular["latest_date"],
            series=regular["series"],
        )
        diesel_rows = self.repository.replace_history(
            fuel_type="diesel",
            latest_date=diesel["latest_date"],
            series=diesel["series"],
        )

        return [
            {
                "dataset": "regular_history",
                "latest_date": regular["latest_date"],
                "rows": regular_rows,
            },
            {
                "dataset": "diesel_history",
                "latest_date": diesel["latest_date"],
                "rows": diesel_rows,
            },
        ]

    def refresh_all(self) -> dict[str, Any]:
        current = self.refresh_current_prices()
        histories = self.refresh_histories()
        return {"current": current, "histories": histories}
