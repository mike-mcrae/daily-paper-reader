import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/papers.db")


def resolve_database_path() -> Path:
    db_path = Path(DATABASE_PATH)
    if db_path.is_absolute():
        return db_path
    return BASE_DIR / db_path


def get_db():
    db_path = resolve_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            year INTEGER,
            source TEXT,
            field TEXT,
            type TEXT,
            citation_proxy INTEGER DEFAULT 0,
            url TEXT,
            summary_text TEXT
        );

        CREATE TABLE IF NOT EXISTS user_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'saved',
            date_added TEXT NOT NULL DEFAULT (date('now')),
            last_updated TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER NOT NULL UNIQUE,
            summary TEXT DEFAULT '',
            key_findings TEXT DEFAULT '',
            contribution TEXT DEFAULT '',
            methodology TEXT DEFAULT '',
            assumptions_stated TEXT DEFAULT '',
            assumptions_unstated TEXT DEFAULT '',
            improvements TEXT DEFAULT '',
            quotes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        );

        CREATE TABLE IF NOT EXISTS daily_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            paper_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'shown',
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            total_read INTEGER DEFAULT 0,
            total_fully_noted INTEGER DEFAULT 0,
            last_active_date TEXT
        );
    """)
    # Ensure a single user_stats row exists
    row = conn.execute("SELECT COUNT(*) FROM user_stats").fetchone()
    if row[0] == 0:
        conn.execute("INSERT INTO user_stats DEFAULT VALUES")
    conn.execute(
        """INSERT INTO user_papers (paper_id, status)
           SELECT n.paper_id, 'saved'
           FROM notes n
           LEFT JOIN user_papers up ON up.paper_id = n.paper_id
           WHERE up.paper_id IS NULL"""
    )
    conn.commit()
    conn.close()
