# modules/announce.py
from db import connect
from datetime import datetime

def add_announce(text: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO announcements (text, date_created) VALUES (?, ?)", (text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_announcements():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT text, date_created FROM announcements ORDER BY date_created DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
