from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from active_recall_pipeline.config import STAGE_ORDER, Stage


class SQLiteManager:
    """Manages SQLite database operations for the pipeline."""

    def __init__(self, db_path: Path | None = None):
        """Initialize database manager and create tables if needed."""
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "pipeline.db"

        self.db_path = db_path
        self._lock = threading.Lock()

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

    def _init_schema(self) -> None:
        """Create all tables if they don't exist."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Chapters table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chapters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        book TEXT NOT NULL,
                        chapter_num INTEGER NOT NULL,
                        chapter_title TEXT NOT NULL,
                        pdf_path TEXT NOT NULL UNIQUE,
                        input_mode TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)

                # Stage runs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stage_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chapter_id INTEGER REFERENCES chapters(id),
                        stage TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        validation_status TEXT DEFAULT 'pending',
                        validation_errors TEXT,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        UNIQUE(chapter_id, stage)
                    )
                """)

                # API calls table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_calls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chapter_id INTEGER REFERENCES chapters(id),
                        stage TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        model TEXT NOT NULL,
                        tier INTEGER NOT NULL,
                        input_tokens INTEGER,
                        output_tokens INTEGER,
                        cost_usd REAL,
                        duration_seconds REAL,
                        success INTEGER DEFAULT 1,
                        error_type TEXT,
                        called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Cost ledger table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cost_ledger (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chapter_id INTEGER REFERENCES chapters(id),
                        provider TEXT NOT NULL,
                        tier INTEGER NOT NULL,
                        total_input_tokens INTEGER DEFAULT 0,
                        total_output_tokens INTEGER DEFAULT 0,
                        total_cost_usd REAL DEFAULT 0.0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(chapter_id, provider, tier)
                    )
                """)

                conn.commit()

    # =========================================================================
    # Chapter methods
    # =========================================================================

    def upsert_chapter(
        self,
        exam: str,
        subject: str,
        book: str,
        chapter_num: int,
        chapter_title: str,
        pdf_path: str,
        input_mode: str,
    ) -> int:
        """Insert or ignore chapter. Return chapter_id."""
        pdf_path = str(Path(pdf_path).resolve())
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO chapters
                    (exam, subject, book, chapter_num, chapter_title, pdf_path, input_mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (exam, subject, book, chapter_num, chapter_title, pdf_path, input_mode),
                )

                conn.commit()

                # Return chapter_id
                cursor.execute("SELECT id FROM chapters WHERE pdf_path = ?", (pdf_path,))
                result = cursor.fetchone()
                return result[0] if result else None

    def get_chapter_id(self, pdf_path: str) -> int | None:
        """Return chapter_id for given pdf_path or None."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM chapters WHERE pdf_path = ?", (pdf_path,))
                result = cursor.fetchone()
                return result[0] if result else None

    def set_chapter_status(self, chapter_id: int, status: str) -> None:
        """Update chapter status and completed_at if status=completed."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if status == "completed":
                    cursor.execute(
                        "UPDATE chapters SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (status, chapter_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE chapters SET status = ? WHERE id = ?",
                        (status, chapter_id),
                    )

                conn.commit()

    def get_pending_chapters(self) -> list[dict]:
        """Return all chapters where status != completed and != failed."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM chapters WHERE status NOT IN ('completed', 'failed')"
                )

                return [dict(row) for row in cursor.fetchall()]

    def get_all_chapters(self) -> list[dict]:
        """Return all chapters regardless of status."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM chapters")

                return [dict(row) for row in cursor.fetchall()]

    # =========================================================================
    # Stage methods
    # =========================================================================

    def init_stage_runs(self, chapter_id: int) -> None:
        """Insert a row for every stage with status=pending if not exists."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for stage in STAGE_ORDER:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO stage_runs
                        (chapter_id, stage, status)
                        VALUES (?, ?, 'pending')
                        """,
                        (chapter_id, stage.value),
                    )

                conn.commit()

    def get_stage_status(self, chapter_id: int, stage: str) -> dict | None:
        """Return full stage_runs row as dict or None."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM stage_runs WHERE chapter_id = ? AND stage = ?",
                    (chapter_id, stage),
                )

                row = cursor.fetchone()
                return dict(row) if row else None

    def set_stage_status(
        self,
        chapter_id: int,
        stage: str,
        status: str,
        error_message: str = None,
    ) -> None:
        """Update stage status, timestamps, and error message."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if status == "running":
                    cursor.execute(
                        """
                        UPDATE stage_runs
                        SET status = ?, started_at = CURRENT_TIMESTAMP, error_message = ?
                        WHERE chapter_id = ? AND stage = ?
                        """,
                        (status, error_message, chapter_id, stage),
                    )
                elif status in ("completed", "failed"):
                    cursor.execute(
                        """
                        UPDATE stage_runs
                        SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                        WHERE chapter_id = ? AND stage = ?
                        """,
                        (status, error_message, chapter_id, stage),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE stage_runs
                        SET status = ?, error_message = ?
                        WHERE chapter_id = ? AND stage = ?
                        """,
                        (status, error_message, chapter_id, stage),
                    )

                conn.commit()

    def set_validation_status(
        self,
        chapter_id: int,
        stage: str,
        validation_status: str,
        validation_errors: list = None,
    ) -> None:
        """Update validation status and errors (serialize as JSON)."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                errors_json = json.dumps(validation_errors) if validation_errors else None

                cursor.execute(
                    """
                    UPDATE stage_runs
                    SET validation_status = ?, validation_errors = ?
                    WHERE chapter_id = ? AND stage = ?
                    """,
                    (validation_status, errors_json, chapter_id, stage),
                )

                conn.commit()

    def _stage_completed_unsafe(self, conn: sqlite3.Connection, chapter_id: int, stage: str) -> bool:
        """Return True only if status=completed AND validation_status=passed.
        Caller must already hold self._lock and pass an open connection.
        """
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM stage_runs
            WHERE chapter_id = ? AND stage = ?
            AND status = 'completed' AND validation_status = 'passed'
            """,
            (chapter_id, stage),
        )
        return cursor.fetchone() is not None

    def stage_completed(self, chapter_id: int, stage: str) -> bool:
        """Return True only if status=completed AND validation_status=passed."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                return self._stage_completed_unsafe(conn, chapter_id, stage)

    def increment_retry(self, chapter_id: int, stage: str) -> int:
        """Increment retry_count and return new count."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE stage_runs
                    SET retry_count = retry_count + 1
                    WHERE chapter_id = ? AND stage = ?
                    """,
                    (chapter_id, stage),
                )

                cursor.execute(
                    "SELECT retry_count FROM stage_runs WHERE chapter_id = ? AND stage = ?",
                    (chapter_id, stage),
                )

                result = cursor.fetchone()
                conn.commit()

                return result[0] if result else 0

    def get_actionable_stages(self, chapter_id: int) -> list[str]:
        """Return stages where:
        - status = pending or failed
        - previous stage is completed and validation passed
        - retry_count < 3
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT stage, retry_count FROM stage_runs
                    WHERE chapter_id = ? AND status IN ('pending', 'failed')
                    AND retry_count < 3
                    """,
                    (chapter_id,),
                )

                stages = [row["stage"] for row in cursor.fetchall()]

                actionable = []
                stage_values = [s.value for s in STAGE_ORDER]
                for stage_name in stages:
                    try:
                        current_idx = stage_values.index(stage_name)
                        if current_idx == 0:
                            # First stage — no predecessor, always actionable
                            actionable.append(stage_name)
                        else:
                            # Use unsafe variant — we already hold self._lock
                            prev_stage = stage_values[current_idx - 1]
                            if self._stage_completed_unsafe(conn, chapter_id, prev_stage):
                                actionable.append(stage_name)
                    except ValueError:
                        # Stage not in STAGE_ORDER, skip
                        pass

                return actionable

    # =========================================================================
    # API call logging methods
    # =========================================================================

    def log_api_call(
        self,
        chapter_id: int,
        stage: str,
        provider: str,
        model: str,
        tier: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_seconds: float,
        success: int = 1,
        error_type: str = None,
    ) -> None:
        """Log one API call."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO api_calls
                    (chapter_id, stage, provider, model, tier, input_tokens, output_tokens,
                     cost_usd, duration_seconds, success, error_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chapter_id,
                        stage,
                        provider,
                        model,
                        tier,
                        input_tokens,
                        output_tokens,
                        cost_usd,
                        duration_seconds,
                        success,
                        error_type,
                    ),
                )

                conn.commit()

    def update_cost_ledger(
        self,
        chapter_id: int,
        provider: str,
        tier: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """Upsert cost_ledger — add to totals if exists, insert if not."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO cost_ledger
                    (chapter_id, provider, tier, total_input_tokens, total_output_tokens, total_cost_usd)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(chapter_id, provider, tier) DO UPDATE SET
                        total_input_tokens = total_input_tokens + excluded.total_input_tokens,
                        total_output_tokens = total_output_tokens + excluded.total_output_tokens,
                        total_cost_usd = total_cost_usd + excluded.total_cost_usd,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (chapter_id, provider, tier, input_tokens, output_tokens, cost_usd),
                )

                conn.commit()

    # =========================================================================
    # Reporting methods
    # =========================================================================

    def get_chapter_cost_summary(self, chapter_id: int) -> dict:
        """Return total cost per provider for this chapter."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT provider, total_input_tokens, total_output_tokens, total_cost_usd
                    FROM cost_ledger
                    WHERE chapter_id = ?
                    """,
                    (chapter_id,),
                )

                result = {}
                for row in cursor.fetchall():
                    provider = row[0]
                    result[provider] = {
                        "input_tokens": row[1],
                        "output_tokens": row[2],
                        "cost_usd": row[3],
                    }

                return result

    def get_pipeline_summary(self) -> dict:
        """Return total cost across all chapters all providers."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT provider, SUM(total_input_tokens), SUM(total_output_tokens), SUM(total_cost_usd)
                    FROM cost_ledger
                    GROUP BY provider
                    """
                )

                result = {}
                for row in cursor.fetchall():
                    provider = row[0]
                    result[provider] = {
                        "input_tokens": row[1] or 0,
                        "output_tokens": row[2] or 0,
                        "cost_usd": row[3] or 0.0,
                    }

                return result