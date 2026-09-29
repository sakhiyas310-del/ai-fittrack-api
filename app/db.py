"""
Database access layer.

This project uses Python's built-in `sqlite3` module directly instead of
an ORM. For a small, beginner-friendly project this keeps things simple
and transparent: every SQL statement is visible right here, and there is
no extra library to install just to talk to the database.

The database file is created automatically the first time the app runs.
"""

import os
import sqlite3

DB_PATH = os.environ.get(
    "DATABASE_PATH", os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "fittrack.db")
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    height_cm REAL NOT NULL,
    weight_kg REAL NOT NULL,
    fitness_goal TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    workout_days_per_week INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_name TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    calories INTEGER NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weight_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight_kg REAL NOT NULL,
    date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS water_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_ml INTEGER NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""


def get_connection():
    """
    Open a new connection to the SQLite database.

    `row_factory = sqlite3.Row` lets us access columns by name (like a
    dict) instead of by numeric index, which makes the route code much
    more readable.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't already exist. Safe to call every startup."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        # Login columns are added separately so databases created by older versions keep working.
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)")]
        if "email" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "password_hash" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)")
        conn.commit()
    finally:
        conn.close()
