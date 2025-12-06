# modules/homework.py
from db import connect
from datetime import datetime

def add_hw(subject: str, text: str, due_date: str = None):
    conn = connect()
    cur = conn.cursor()
    if due_date is None:
        due_date = datetime.now().date().isoformat()
    # удаляем старые задания с таким subject и due_date (чтобы не плодить)
    cur.execute("DELETE FROM homework WHERE subject=? AND due_date=?", (subject, due_date))
    cur.execute("INSERT INTO homework (subject, text, due_date, date_added) VALUES (?, ?, ?, ?)",
                (subject, text, due_date, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_hw(subject: str = None):
    conn = connect()
    cur = conn.cursor()
    if subject:
        cur.execute("SELECT subject, text, due_date, date_added FROM homework WHERE subject=? ORDER BY due_date", (subject,))
    else:
        cur.execute("SELECT subject, text, due_date, date_added FROM homework ORDER BY due_date")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_hw(subject: str, due_date: str = None):
    conn = connect()
    cur = conn.cursor()
    if due_date:
        cur.execute("DELETE FROM homework WHERE subject=? AND due_date=?", (subject, due_date))
    else:
        cur.execute("DELETE FROM homework WHERE subject=?", (subject,))
    conn.commit()
    conn.close()
