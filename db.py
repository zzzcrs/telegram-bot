# db.py
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "school.db"

def connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS schedule(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weekday INTEGER,
        lesson_number INTEGER,
        subject TEXT,
        room TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS homework(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        text TEXT,
        due_date TEXT,
        date_added TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        test_date TEXT,
        description TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        mark INTEGER,
        date_added TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS announcements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        date_created TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        ts TEXT
    );
    """)

    conn.commit()
    conn.close()

# simple helpers
def add_user(user_id: int, username: Optional[str]):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?,?)", (user_id, username))
    conn.commit()
    conn.close()

def log_action(user_id, action):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (user_id, action, ts) VALUES (?, ?, ?)",
                (user_id, action, datetime.now().isoformat()))
    conn.commit()
    conn.close()
