import sqlite3

DB_PATH = "bot_db.sqlite"

def init():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weekday INTEGER,
            lesson_number INTEGER,
            subject TEXT,
            room TEXT
        )
        """)
        conn.commit()

def add_schedule_entry(weekday, lesson_number, subject, room):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO schedule (weekday, lesson_number, subject, room) VALUES (?, ?, ?, ?)",
                    (weekday, lesson_number, subject, room))
        conn.commit()

def get_day_schedule(weekday):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT lesson_number, subject, room FROM schedule WHERE weekday=? ORDER BY lesson_number", (weekday,))
        return cur.fetchall()

def get_week_schedule():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT weekday, lesson_number, subject, room FROM schedule ORDER BY weekday, lesson_number")
        return cur.fetchall()
