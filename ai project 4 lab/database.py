"""
Database Module – AI Lost & Found Intelligence System
"""

import sqlite3
import os
from flask_bcrypt import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "lost_found.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            image_path TEXT,
            contact TEXT,
            timestamp TEXT NOT NULL,
            priority_level TEXT DEFAULT 'MEDIUM',
            is_flagged INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS found_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            image_path TEXT,
            contact TEXT,
            timestamp TEXT NOT NULL,
            priority_level TEXT DEFAULT 'MEDIUM',
            is_flagged INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Try adding user_id to existing items tables (if adapting existing db)
    # Defaulting to 1 for generic existing records
    try:
        cursor.execute("ALTER TABLE lost_items ADD COLUMN user_id INTEGER DEFAULT 1")
        cursor.execute("ALTER TABLE found_items ADD COLUMN user_id INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Check if admin exists
    admin = cursor.execute("SELECT id FROM users WHERE email='admin@gmail.com'").fetchone()
    if not admin:
        hashed_pw = generate_password_hash("Admin123").decode('utf-8')
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("System Admin", "admin@gmail.com", hashed_pw, "admin")
        )

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")

if __name__ == "__main__":
    init_db()
