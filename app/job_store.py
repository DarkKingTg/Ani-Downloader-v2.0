"""SQLite persistence for download jobs."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Dict, Any, List


class JobStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id INTEGER PRIMARY KEY,
                    anime_url TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def upsert_job(self, job_id: int, anime_url: str, config: Dict[str, Any], state: Dict[str, Any]) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO jobs(job_id, anime_url, config_json, state_json, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(job_id) DO UPDATE SET
                        anime_url=excluded.anime_url,
                        config_json=excluded.config_json,
                        state_json=excluded.state_json,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (job_id, anime_url, json.dumps(config, ensure_ascii=False), json.dumps(state, ensure_ascii=False)),
                )
                conn.commit()

    def delete_job(self, job_id: int) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
                conn.commit()

    def load_jobs(self) -> List[Dict[str, Any]]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute("SELECT job_id, anime_url, config_json, state_json FROM jobs ORDER BY job_id ASC").fetchall()

        result = []
        for r in rows:
            try:
                result.append(
                    {
                        "job_id": int(r["job_id"]),
                        "anime_url": r["anime_url"],
                        "config": json.loads(r["config_json"]),
                        "state": json.loads(r["state_json"]),
                    }
                )
            except Exception:
                continue
        return result

    def get_max_job_id(self) -> int:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute("SELECT COALESCE(MAX(job_id), 0) AS max_id FROM jobs").fetchone()
        return int(row["max_id"]) if row else 0
