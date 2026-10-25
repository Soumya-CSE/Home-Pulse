from __future__ import annotations
import sqlite3
from contextlib import closing
from pathlib import Path
import pandas as pd
from .config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    run_id TEXT, ts TEXT, room TEXT,
    temperature REAL, humidity REAL, aqi REAL, lux REAL, motion INTEGER
);
CREATE TABLE IF NOT EXISTS power (
    run_id TEXT, ts TEXT, power_w REAL, energy_kwh REAL, mode TEXT
);
CREATE TABLE IF NOT EXISTS events (
    run_id TEXT, ts TEXT, category TEXT, level TEXT, message TEXT
);
CREATE INDEX IF NOT EXISTS idx_readings_run ON readings(run_id);
CREATE INDEX IF NOT EXISTS idx_power_run ON power(run_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
"""



class Database:
    def __init__(self, path: str | Path = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    # ----------------------------------------------------------------- writes
    def log_snapshot(self, run_id: str, snap: dict) -> None:
        ts = snap["time"].isoformat(timespec="minutes")
        rows = [
            (run_id, ts, room, r["temperature"], r["humidity"], r["aqi"], r["lux"], int(r["motion"]))
            for room, r in snap["rooms"].items()
        ]
        with closing(self._connect()) as conn, conn:
            conn.executemany("INSERT INTO readings VALUES (?,?,?,?,?,?,?,?)", rows)
            conn.execute(
                "INSERT INTO power VALUES (?,?,?,?,?)",
                (run_id, ts, snap["power"], snap["energy_kwh"], snap["mode"]),
            )

    def log_event(self, run_id: str, ts, category: str, level: str, message: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (run_id, ts.isoformat(timespec="minutes"), category, level, message),
            )

    def clear(self, run_id: str | None = None) -> None:
        with closing(self._connect()) as conn, conn:
            for table in ("readings", "power", "events"):
                if run_id:
                    conn.execute(f"DELETE FROM {table} WHERE run_id = ?", (run_id,))
                else:
                    conn.execute(f"DELETE FROM {table}")

    # ------------------------------------------------------------------ reads
    def _query(self, sql: str, run_id: str, time_col: str = "time") -> pd.DataFrame:
        with closing(self._connect()) as conn:
            df = pd.read_sql_query(sql, conn, params=(run_id,))
        if not df.empty:
            df[time_col] = pd.to_datetime(df[time_col])
        return df

    def readings(self, run_id: str) -> pd.DataFrame:
        return self._query(
            "SELECT ts AS time, room, temperature, humidity, aqi, lux, motion "
            "FROM readings WHERE run_id = ? ORDER BY ts",
            run_id,
        )

    def power(self, run_id: str) -> pd.DataFrame:
        return self._query(
            "SELECT ts AS time, power_w, energy_kwh, mode FROM power WHERE run_id = ? ORDER BY ts",
            run_id,
        )

    def events(self, run_id: str) -> pd.DataFrame:
        return self._query(
            "SELECT ts AS time, category, level, message FROM events "
            "WHERE run_id = ? ORDER BY ts DESC, rowid DESC",
            run_id,
        )
