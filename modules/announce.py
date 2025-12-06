from db import connect
from datetime import datetime

def add_announce(text: str):
    """Добавить объявление"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO announcements (text, date_created) VALUES (?, ?)",
                (text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_announcements(limit: int = 20):
    """Получить все объявления"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT text, date_created FROM announcements ORDER BY date_created DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_recent_announcements(days: int = 7):
    """Получить свежие объявления за последние дни"""
    conn = connect()
    cur = conn.cursor()
    date_limit = (datetime.now() - datetime.timedelta(days=days)).isoformat()
    cur.execute("SELECT text, date_created FROM announcements WHERE date_created > ? ORDER BY date_created DESC",
                (date_limit,))
    rows = cur.fetchall()
    conn.close()
    return rows