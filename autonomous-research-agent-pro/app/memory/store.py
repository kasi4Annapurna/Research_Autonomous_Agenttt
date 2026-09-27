import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "research_agent.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection() -> sqlite3.Connection:
    """
    Create a SQLite connection.

    row_factory allows us to access columns by name.
    """
    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db() -> None:
    """
    Create the required tables if they don't already exist.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                query TEXT NOT NULL,

                report TEXT,

                search_queries TEXT,

                source_count INTEGER DEFAULT 0,

                research_rounds INTEGER DEFAULT 1,

                markdown_path TEXT,

                pdf_path TEXT,

                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# SAVE RESEARCH SESSION
# ============================================================

def save(
    query: str,
    report: str,
    search_queries: Optional[List[str]] = None,
    source_count: int = 0,
    research_rounds: int = 1,
    markdown_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
) -> int:
    """
    Save a completed research session.

    Returns:
        Database ID of the newly created session.
    """

    init_db()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        created_at = datetime.now(timezone.utc).isoformat()

        search_queries_json = json.dumps(
            search_queries or [],
            ensure_ascii=False,
        )

        cursor.execute(
            """
            INSERT INTO research_sessions (
                query,
                report,
                search_queries,
                source_count,
                research_rounds,
                markdown_path,
                pdf_path,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                query,
                report,
                search_queries_json,
                source_count,
                research_rounds,
                markdown_path,
                pdf_path,
                created_at,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# ============================================================
# GET ALL SESSIONS
# ============================================================

def load() -> List[Dict[str, Any]]:
    """
    Return all research sessions.

    Newest sessions are returned first.
    """

    init_db()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM research_sessions
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()

        sessions = []

        for row in rows:
            item = dict(row)

            try:
                item["search_queries"] = json.loads(
                    item.get("search_queries") or "[]"
                )
            except json.JSONDecodeError:
                item["search_queries"] = []

            sessions.append(item)

        return sessions

    finally:
        connection.close()


# ============================================================
# GET ONE SESSION
# ============================================================

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve one research session by ID.
    """

    init_db()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM research_sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        item = dict(row)

        try:
            item["search_queries"] = json.loads(
                item.get("search_queries") or "[]"
            )
        except json.JSONDecodeError:
            item["search_queries"] = []

        return item

    finally:
        connection.close()


# ============================================================
# DELETE ONE SESSION
# ============================================================

def delete_session(session_id: int) -> bool:
    """
    Delete one research session.

    Returns:
        True if a record was deleted.
    """

    init_db()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM research_sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# ============================================================
# CLEAR ALL MEMORY
# ============================================================

def clear_all() -> None:
    """
    Delete all stored research sessions.
    """

    init_db()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM research_sessions
            """
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# DATABASE STATS
# ============================================================

def count_sessions() -> int:
    """
    Return total number of stored research sessions.
    """

    init_db()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM research_sessions
            """
        )

        result = cursor.fetchone()

        return int(result[0])

    finally:
        connection.close()


# ============================================================
# INITIALIZE DATABASE ON IMPORT
# ============================================================

init_db()