from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS captures (
  id TEXT PRIMARY KEY,
  content TEXT NOT NULL,
  hint TEXT,
  content_type TEXT NOT NULL,
  source_url TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  capture_id TEXT NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  commit_sha TEXT,
  FOREIGN KEY (capture_id) REFERENCES captures(id)
);

CREATE TABLE IF NOT EXISTS job_attempts (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  log_path TEXT,
  error TEXT,
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS changed_files (
  id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  path TEXT NOT NULL,
  change_type TEXT NOT NULL,
  validation_status TEXT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL,
  metadata_json TEXT,
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS validation_failures (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  path TEXT NOT NULL,
  code TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS embedding_queue (
  id TEXT PRIMARY KEY,
  note_path TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS note_index (
  path TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body_preview TEXT NOT NULL,
  tags TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plugin_recommendations (
  id TEXT PRIMARY KEY,
  plugin_id TEXT NOT NULL,
  status TEXT NOT NULL,
  rationale TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_checks (
  id TEXT PRIMARY KEY,
  check_name TEXT NOT NULL,
  ok INTEGER NOT NULL,
  message TEXT NOT NULL,
  checked_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


class Store:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def create_capture(
        self,
        *,
        content: str,
        hint: str | None,
        content_type: str,
        source_url: str | None = None,
    ) -> dict[str, Any]:
        capture = {
            "id": str(uuid.uuid4()),
            "content": content,
            "hint": hint,
            "content_type": content_type,
            "source_url": source_url,
            "created_at": now_iso(),
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO captures (id, content, hint, content_type, source_url, created_at)
                VALUES (:id, :content, :hint, :content_type, :source_url, :created_at)
                """,
                capture,
            )
        return capture

    def create_job(self, *, capture_id: str, job_type: str) -> dict[str, Any]:
        timestamp = now_iso()
        job = {
            "id": str(uuid.uuid4()),
            "capture_id": capture_id,
            "job_type": job_type,
            "status": "queued",
            "created_at": timestamp,
            "updated_at": timestamp,
            "attempts": 0,
            "last_error": None,
            "commit_sha": None,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs
                (id, capture_id, job_type, status, created_at, updated_at, attempts, last_error, commit_sha)
                VALUES
                (:id, :capture_id, :job_type, :status, :created_at, :updated_at, :attempts, :last_error, :commit_sha)
                """,
                job,
            )
        return job

    def queue_action_needed_jobs(self) -> list[dict[str, Any]]:
        queued: list[dict[str, Any]] = []
        timestamp = now_iso()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT original.capture_id, original.job_type
                FROM jobs AS original
                WHERE original.status IN ('needs_rerun', 'needs_review')
                  AND NOT EXISTS (
                    SELECT 1
                    FROM jobs AS newer
                    WHERE newer.capture_id = original.capture_id
                      AND newer.job_type = original.job_type
                      AND (
                        newer.created_at > original.created_at
                        OR (newer.created_at = original.created_at AND newer.rowid > original.rowid)
                      )
                  )
                  AND NOT EXISTS (
                    SELECT 1
                    FROM jobs AS active
                    WHERE active.capture_id = original.capture_id
                      AND active.job_type = original.job_type
                      AND active.status IN ('queued', 'running')
                  )
                GROUP BY original.capture_id, original.job_type
                ORDER BY MIN(original.created_at)
                """
            ).fetchall()
            for row in rows:
                job = {
                    "id": str(uuid.uuid4()),
                    "capture_id": row["capture_id"],
                    "job_type": row["job_type"],
                    "status": "queued",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "attempts": 0,
                    "last_error": None,
                    "commit_sha": None,
                }
                conn.execute(
                    """
                    INSERT INTO jobs
                    (id, capture_id, job_type, status, created_at, updated_at, attempts, last_error, commit_sha)
                    VALUES
                    (:id, :capture_id, :job_type, :status, :created_at, :updated_at, :attempts, :last_error, :commit_sha)
                    """,
                    job,
                )
                queued.append(job)
        return queued

    def get_capture(self, capture_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM captures WHERE id = ?", (capture_id,)).fetchone()
        return row_to_dict(row) if row else None

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return row_to_dict(row) if row else None

    def next_queued_job(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
        return row_to_dict(row) if row else None

    def claim_next_queued_job(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            job_id = row["id"]
            conn.execute(
                """
                UPDATE jobs
                SET status = 'running', updated_at = ?, attempts = attempts + 1, last_error = NULL
                WHERE id = ? AND status = 'queued'
                """,
                (now_iso(), job_id),
            )
            claimed = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return row_to_dict(claimed) if claimed else None

    def requeue_stale_running_jobs(self, *, older_than_seconds: int) -> list[dict[str, Any]]:
        if older_than_seconds <= 0:
            return []
        cutoff = datetime.now(timezone.utc).timestamp() - older_than_seconds
        requeued: list[dict[str, Any]] = []
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM jobs WHERE status = 'running'").fetchall()
            for row in rows:
                updated_at = datetime.fromisoformat(row["updated_at"]).timestamp()
                if updated_at > cutoff:
                    continue
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = 'queued', updated_at = ?, last_error = ?
                    WHERE id = ? AND status = 'running'
                    """,
                    (
                        now_iso(),
                        "Stale running job requeued after worker interruption.",
                        row["id"],
                    ),
                )
                refreshed = conn.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
                if refreshed:
                    requeued.append(row_to_dict(refreshed))
        return requeued

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT rowid AS _rowid, * FROM jobs ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        jobs = [row_to_dict(row) for row in rows]
        latest_keys: set[tuple[str, str]] = set()
        for job in jobs:
            key = (job["capture_id"], job["job_type"])
            job["superseded"] = key in latest_keys
            job.pop("_rowid", None)
            latest_keys.add(key)
        return jobs

    def update_job(
        self,
        job_id: str,
        *,
        status: str,
        last_error: str | None = None,
        commit_sha: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = ?, last_error = ?, commit_sha = COALESCE(?, commit_sha)
                WHERE id = ?
                """,
                (status, now_iso(), last_error, commit_sha, job_id),
            )

    def add_audit_event(self, *, job_id: str | None, event_type: str, message: str) -> dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "job_id": job_id,
            "event_type": event_type,
            "message": message,
            "created_at": now_iso(),
            "metadata_json": None,
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, job_id, event_type, message, created_at, metadata_json)
                VALUES (:id, :job_id, :event_type, :message, :created_at, :metadata_json)
                """,
                event,
            )
        return event
