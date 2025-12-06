# modules/schedule.py
from db import connect

def get_day_schedule(weekday: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT lesson_number, subject, room
        FROM schedule
        WHERE weekday = ?
        ORDER BY lesson_number
    """, (weekday,))
    data = cur.fetchall()
    conn.close()
    return data

def add_schedule_entry(weekday, number, subject, room):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO schedule (weekday, lesson_number, subject, room) VALUES (?, ?, ?, ?)",
                (weekday, number, subject, room))
    conn.commit()
    conn.close()

def get_week_schedule():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT weekday, lesson_number, subject, room FROM schedule ORDER BY weekday, lesson_number")
    rows = cur.fetchall()
    conn.close()
    return rows
