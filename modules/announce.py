import sqlite3
from datetime import datetime

DB_PATH = "bot_db.sqlite"

def add_announce(text: str):
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
