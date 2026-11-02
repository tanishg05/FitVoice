"""SQLite database initialization and connection management."""

import sqlite3
import os
from pathlib import Path
from fitvoice.config import settings


def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    """Obtain a SQLite connection with Row factory enabled."""
    target_path = db_path or settings.db_path
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = None) -> None:
    """Initialize database tables with parameterized indexes and integrity constraints."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS workout_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        session_name TEXT NOT NULL,
        duration_minutes INTEGER,
        status TEXT NOT NULL DEFAULT 'CONFIRMED',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS workout_sets (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        exercise TEXT NOT NULL,
        weight_kg REAL NOT NULL,
        reps INTEGER NOT NULL,
        rpe REAL,
        notes TEXT,
        FOREIGN KEY (session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS recovery_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        sleep_hours REAL NOT NULL,
        soreness_score INTEGER,
        energy_score INTEGER,
        readiness_score INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS nutrition_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        item TEXT NOT NULL,
        calories REAL,
        protein_g REAL,
        carbs_g REAL,
        fat_g REAL,
        status TEXT NOT NULL DEFAULT 'CONFIRMED',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS measurements (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        metric_name TEXT NOT NULL,
        value REAL NOT NULL,
        unit TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'CONFIRMED',
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_date ON workout_sessions(user_id, date);
    CREATE INDEX IF NOT EXISTS idx_workout_sets_user_exercise ON workout_sets(user_id, exercise);
    CREATE INDEX IF NOT EXISTS idx_recovery_logs_user_date ON recovery_logs(user_id, date);
    """)

    conn.commit()
    conn.close()

