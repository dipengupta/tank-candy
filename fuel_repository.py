from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class FuelRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS daily_state_prices (
                    snapshot_date TEXT NOT NULL,
                    state_code TEXT NOT NULL,
                    regular REAL NOT NULL,
                    mid_grade REAL,
                    premium REAL,
                    diesel REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (snapshot_date, state_code)
                );

                CREATE TABLE IF NOT EXISTS fuel_history (
                    fuel_type TEXT NOT NULL,
                    series_key TEXT NOT NULL,
                    week_start TEXT NOT NULL,
                    price REAL NOT NULL,
                    PRIMARY KEY (fuel_type, series_key, week_start)
                );

                CREATE INDEX IF NOT EXISTS idx_fuel_history_lookup
                ON fuel_history (fuel_type, series_key, week_start);

                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def bootstrap_from_seed(self, seed_path: str | Path) -> bool:
        if self.has_any_data():
            return False

        seed_file = Path(seed_path)
        if not seed_file.exists():
            return False

        payload = json.loads(seed_file.read_text())
        with self._connect() as connection:
            for item in payload.get("daily_snapshots", []):
                snapshot_date = item["snapshot_date"]
                for state_code, prices in item["states"].items():
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO daily_state_prices (
                            snapshot_date, state_code, regular, mid_grade, premium, diesel
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            snapshot_date,
                            state_code,
                            prices["regular"],
                            prices.get("mid_grade"),
                            prices.get("premium"),
                            prices["diesel"],
                        ),
                    )

            for fuel_type, history in payload.get("history", {}).items():
                for series_key, points in history.get("series", {}).items():
                    if isinstance(points, dict):
                        rows = [
                            (fuel_type, series_key, week_start, price)
                            for week_start, price in zip(
                                points.get("dates", []),
                                points.get("values", []),
                                strict=True,
                            )
                        ]
                    else:
                        rows = [
                            (fuel_type, series_key, week_start, price)
                            for week_start, price in points
                        ]
                    connection.executemany(
                        """
                        INSERT OR REPLACE INTO fuel_history (
                            fuel_type, series_key, week_start, price
                        ) VALUES (?, ?, ?, ?)
                        """,
                        rows,
                    )

                latest_date = history.get("latest_date")
                if latest_date:
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO metadata (key, value)
                        VALUES (?, ?)
                        """,
                        (f"{fuel_type}_history_latest_date", latest_date),
                    )

            for key, value in payload.get("metadata", {}).items():
                connection.execute(
                    """
                    INSERT OR REPLACE INTO metadata (key, value)
                    VALUES (?, ?)
                    """,
                    (key, value),
                )

        return True

    def has_any_data(self) -> bool:
        with self._connect() as connection:
            current_count = connection.execute(
                "SELECT COUNT(*) FROM daily_state_prices"
            ).fetchone()[0]
            history_count = connection.execute(
                "SELECT COUNT(*) FROM fuel_history"
            ).fetchone()[0]
        return bool(current_count or history_count)

    def upsert_daily_snapshot(
        self, snapshot_date: str, states: dict[str, dict[str, float]]
    ) -> int:
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO daily_state_prices (
                    snapshot_date, state_code, regular, mid_grade, premium, diesel
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        snapshot_date,
                        state_code,
                        prices["regular"],
                        prices.get("mid_grade"),
                        prices.get("premium"),
                        prices["diesel"],
                    )
                    for state_code, prices in states.items()
                ],
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES ('latest_daily_snapshot', ?)
                """,
                (snapshot_date,),
            )
        return len(states)

    def replace_history(
        self,
        fuel_type: str,
        latest_date: str,
        series: dict[str, dict[str, list[Any]]],
    ) -> int:
        rows_to_insert = []
        for series_key, values in series.items():
            rows_to_insert.extend(
                (
                    fuel_type,
                    series_key,
                    week_start,
                    price,
                )
                for week_start, price in zip(values["dates"], values["values"], strict=True)
            )

        with self._connect() as connection:
            connection.execute("DELETE FROM fuel_history WHERE fuel_type = ?", (fuel_type,))
            connection.executemany(
                """
                INSERT INTO fuel_history (fuel_type, series_key, week_start, price)
                VALUES (?, ?, ?, ?)
                """,
                rows_to_insert,
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO metadata (key, value)
                VALUES (?, ?)
                """,
                (f"{fuel_type}_history_latest_date", latest_date),
            )
        return len(rows_to_insert)

    def get_daily_snapshot(
        self, snapshot_date: str, state_code: str
    ) -> dict[str, Any] | None:
        query = """
            SELECT snapshot_date, state_code, regular, mid_grade, premium, diesel
            FROM daily_state_prices
            WHERE snapshot_date = ? AND state_code = ?
        """
        with self._connect() as connection:
            row = connection.execute(query, (snapshot_date, state_code)).fetchone()
        return dict(row) if row else None

    def get_latest_snapshot_on_or_before(
        self, snapshot_date: str, state_code: str
    ) -> dict[str, Any] | None:
        query = """
            SELECT snapshot_date, state_code, regular, mid_grade, premium, diesel
            FROM daily_state_prices
            WHERE snapshot_date <= ? AND state_code = ?
            ORDER BY snapshot_date DESC
            LIMIT 1
        """
        with self._connect() as connection:
            row = connection.execute(query, (snapshot_date, state_code)).fetchone()
        return dict(row) if row else None

    def get_latest_snapshot(self, state_code: str) -> dict[str, Any] | None:
        query = """
            SELECT snapshot_date, state_code, regular, mid_grade, premium, diesel
            FROM daily_state_prices
            WHERE state_code = ?
            ORDER BY snapshot_date DESC
            LIMIT 1
        """
        with self._connect() as connection:
            row = connection.execute(query, (state_code,)).fetchone()
        return dict(row) if row else None

    def get_history_value(
        self, fuel_type: str, series_key: str, target_week: str
    ) -> float | None:
        query = """
            SELECT price
            FROM fuel_history
            WHERE fuel_type = ? AND series_key = ? AND week_start <= ?
            ORDER BY week_start DESC
            LIMIT 1
        """
        with self._connect() as connection:
            row = connection.execute(query, (fuel_type, series_key, target_week)).fetchone()
        return float(row["price"]) if row else None

    def get_earliest_history_date(self, fuel_type: str) -> str | None:
        query = """
            SELECT MIN(week_start) AS earliest
            FROM fuel_history
            WHERE fuel_type = ?
        """
        with self._connect() as connection:
            row = connection.execute(query, (fuel_type,)).fetchone()
        return row["earliest"] if row and row["earliest"] else None

    def get_latest_history_date(self, fuel_type: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT value
                FROM metadata
                WHERE key = ?
                """,
                (f"{fuel_type}_history_latest_date",),
            ).fetchone()
        return row["value"] if row else None

    def get_metadata(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = ?",
                (key,),
            ).fetchone()
        return row["value"] if row else None
