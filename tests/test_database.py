"""Unit tests for database engine and versioned migrations."""

import sqlite3
from pathlib import Path
import pytest
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner


def test_sqlite_wal_and_foreign_keys_enabled(tmp_path: Path):
    db_file = tmp_path / "test_wal.db"
    engine = DatabaseEngine(db_file)
    conn = engine.get_connection()

    # Check WAL mode
    cursor = conn.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    assert mode.lower() == "wal"

    # Check foreign keys
    cursor = conn.execute("PRAGMA foreign_keys;")
    fk_enabled = cursor.fetchone()[0]
    assert fk_enabled == 1

    engine.close()


def test_migration_runner_idempotency(tmp_path: Path):
    db_file = tmp_path / "test_migrations.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)

    # First migration run
    applied_first = migrator.apply_migrations()
    assert applied_first >= 1
    assert migrator.get_current_version() == 2

    # Second migration run (idempotent)
    applied_second = migrator.apply_migrations()
    assert applied_second == 0
    assert migrator.get_current_version() == 2

    engine.close()
