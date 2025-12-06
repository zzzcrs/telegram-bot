# modules/marks.py
from db import connect
from datetime import datetime

def add_mark(user_id: int, subject: str, mark: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO marks (user_id, subject, mark, date_added) VALUES (?, ?, ?, ?)",
                (user_id, subject, mark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_marks(user_id: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT subject, mark FROM marks WHERE user_id = ? ORDER BY subject", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_avg(user_id: int, subject: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT AVG(mark) FROM marks WHERE user_id = ? AND subject = ?", (user_id, subject))
    avg = cur.fetchone()[0]
    conn.close()
    return avg

def clear_marks(user_id: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM marks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
