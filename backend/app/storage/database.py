import json
import sqlite3
import threading
from datetime import datetime
from typing import Optional
from backend.app.core.config import DB_PATH
from backend.app.models.schemas import Memory

_lock = threading.Lock()


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables and indexes."""
    with _lock:
        with get_db_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    iso_timestamp TEXT NOT NULL,
                    screenshot_path TEXT NOT NULL,
                    extracted_text TEXT NOT NULL,
                    application_name TEXT NOT NULL,
                    window_title TEXT NOT NULL,
                    ocr_latency_ms REAL DEFAULT 0.0,
                    embedding_latency_ms REAL DEFAULT 0.0,
                    ocr_status TEXT DEFAULT 'ok',
                    is_demo INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_memories_app ON memories(application_name);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Automatic column migration if database was created prior to ocr_status
            cursor = conn.execute("PRAGMA table_info(memories)")
            columns = [c[1] for c in cursor.fetchall()]
            if "ocr_status" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN ocr_status TEXT DEFAULT 'ok'")


def insert_memory(memory: Memory) -> None:
    with _lock:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories (
                    id, timestamp, iso_timestamp, screenshot_path,
                    extracted_text, application_name, window_title,
                    ocr_latency_ms, embedding_latency_ms, ocr_status, is_demo, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.timestamp,
                    memory.iso_timestamp,
                    memory.screenshot_path,
                    memory.extracted_text,
                    memory.application_name,
                    memory.window_title,
                    memory.ocr_latency_ms,
                    memory.embedding_latency_ms,
                    getattr(memory, "ocr_status", "ok"),
                    1 if memory.is_demo else 0,
                    memory.created_at,
                ),
            )


def get_memory(memory_id: str) -> Optional[Memory]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_memory(row)


def list_memories(
    limit: int = 50,
    offset: int = 0,
    app: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[Memory]:
    query = "SELECT * FROM memories WHERE 1=1"
    params = []

    if app:
        query += " AND application_name = ?"
        params.append(app)

    if date_from:
        query += " AND iso_timestamp >= ?"
        params.append(date_from)

    if date_to:
        query += " AND iso_timestamp <= ?"
        params.append(date_to + "T23:59:59")

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [_row_to_memory(r) for r in rows]


def get_all_memories_for_search() -> list[Memory]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM memories ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [_row_to_memory(r) for r in rows]


def count_memories() -> int:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]


def get_unique_applications() -> list[str]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT DISTINCT application_name FROM memories WHERE application_name != '' ORDER BY application_name ASC")
        return [r[0] for r in cursor.fetchall()]


def delete_memory(memory_id: str) -> bool:
    with _lock:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0


def delete_all_memories() -> int:
    with _lock:
        with get_db_connection() as conn:
            cursor = conn.execute("DELETE FROM memories")
            return cursor.rowcount


def get_setting(key: str, default=None):
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]


def set_setting(key: str, value) -> None:
    val_str = json.dumps(value) if not isinstance(value, str) else value
    now_str = datetime.now().isoformat()
    with _lock:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, val_str, now_str),
            )


def _row_to_memory(row: sqlite3.Row) -> Memory:
    keys = row.keys()
    return Memory(
        id=row["id"],
        timestamp=row["timestamp"],
        iso_timestamp=row["iso_timestamp"],
        screenshot_path=row["screenshot_path"],
        extracted_text=row["extracted_text"],
        application_name=row["application_name"],
        window_title=row["window_title"],
        ocr_latency_ms=row["ocr_latency_ms"],
        embedding_latency_ms=row["embedding_latency_ms"],
        ocr_status=row["ocr_status"] if "ocr_status" in keys else "ok",
        is_demo=bool(row["is_demo"]),
        created_at=row["created_at"],
    )
