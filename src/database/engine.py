"""SQLite Database Engine for Studio-AI.

Guarantees WAL mode, foreign keys enforcement, busy timeout, and transaction safety.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from src.utilities.exceptions import DatabaseError
from src.utilities.logging import get_logger

logger = get_logger()


class DatabaseEngine:
    """SQLite Database Engine with WAL mode and foreign key enforcement."""

    def __init__(self, db_path: Path, busy_timeout: int = 5000):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout = busy_timeout
        self._connection: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        """Get or create active connection with WAL and FK enabled."""
        if self._connection is None:
            try:
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=self.busy_timeout / 1000.0,
                    check_same_thread=False,
                )
                conn.row_factory = sqlite3.Row

                # Configure PRAGMAs
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA foreign_keys=ON;")
                conn.execute(f"PRAGMA busy_timeout={self.busy_timeout};")

                self._connection = conn
                logger.info(f"Database connection opened at {self.db_path} (WAL mode enabled)")
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to connect to SQLite database at {self.db_path}: {e}") from e

        return self._connection

    def close(self) -> None:
        """Close current connection safely."""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.info("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._connection = None

    def execute_in_transaction(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute query within a transaction block."""
        conn = self.get_connection()
        try:
            with conn:
                return conn.execute(query, params)
        except sqlite3.Error as e:
            raise DatabaseError(f"Database transaction error: {e}") from e
