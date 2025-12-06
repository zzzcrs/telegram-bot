import sqlite3
from datetime import datetime

DB_PATH = "bot_db.sqlite"

def init():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            text TEXT,
            due_date TEXT,
            date_added TEXT
        )
        """)
        conn.commit()

def add_hw(subject, text, due_date=None):
    date_added = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO homework (subject, text, due_date, date_added) VALUES (?, ?, ?, ?)",
                    (subject, text, due_date, date_added))
        conn.commit()

def get_hw(subject=None):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if subject:
            cur.execute("SELECT subject, text, due_date, date_added FROM homework WHERE subject=? ORDER BY due_date", (subject,))
        else:
            cur.execute("SELECT subject, text, due_date, date_added FROM homework ORDER BY due_date")
        return cur.fetchall()

def delete_hw(subject, text):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM homework WHERE subject=? AND text=?", (subject, text))
        conn.commit()
