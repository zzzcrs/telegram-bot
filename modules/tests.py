# modules/tests.py
from db import connect
from datetime import datetime

def add_test(subject: str, test_date: str, desc: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO tests (subject, test_date, description) VALUES (?, ?, ?)",
                (subject, test_date, desc))
    conn.commit()
    conn.close()

def get_tests():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT subject, test_date, description FROM tests ORDER BY test_date")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_test(test_id: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM tests WHERE id=?", (test_id,))
    conn.commit()
    conn.close()
