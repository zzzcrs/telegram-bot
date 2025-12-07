from db import connect


def add_schedule_entry(weekday, number, subject, room):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO schedule (weekday, lesson_number, subject, room) VALUES (?, ?, ?, ?)",
                (weekday, number, subject, room))
    conn.commit()
    conn.close()


def get_day_schedule(weekday):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT lesson_number, subject, room FROM schedule WHERE weekday=? ORDER BY lesson_number", (weekday,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_week_schedule():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT weekday, lesson_number, subject, room FROM schedule ORDER BY weekday, lesson_number")
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_schedule(weekday=None, lesson_number=None):
    """Удалить расписание"""
    conn = connect()
    cur = conn.cursor()
    if weekday is not None and lesson_number is not None:
        cur.execute("DELETE FROM schedule WHERE weekday=? AND lesson_number=?", (weekday, lesson_number))
    elif weekday is not None:
        cur.execute("DELETE FROM schedule WHERE weekday=?", (weekday,))
    else:
        cur.execute("DELETE FROM schedule")
    conn.commit()
    conn.close()
