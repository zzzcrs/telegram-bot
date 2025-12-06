import sqlite3
from datetime import datetime

DB_PATH = "bot_db.sqlite"

def init_db():
    from modules import homework, marks, tests, schedule
    homework.init()
    marks.init()
    tests.init()
    schedule.init()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            date_added TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            date_added TEXT
        )
        """)
        conn.commit()

def add_user(user_id, username):
    date_added = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (id, username, date_added) VALUES (?, ?, ?)", (user_id, username, date_added))
        conn.commit()

def log_action(user_id, action):
    print(f"[{datetime.now().isoformat()}] User {user_id}: {action}")

def add_announce(text):
    date_added = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO announcements (text, date_added) VALUES (?, ?)", (text, date_added))
        conn.commit()

def get_all_announcements():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT text, date_added FROM announcements ORDER BY date_added DESC")
        return cur.fetchall()
