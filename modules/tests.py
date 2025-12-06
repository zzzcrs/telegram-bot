import sqlite3

DB_PATH = "bot_db.sqlite"

def init():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            date TEXT,
            description TEXT
        )
        """)
        conn.commit()

def add_test(subject, date, description):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO tests (subject, date, description) VALUES (?, ?, ?)", (subject, date, description))
        conn.commit()

def get_tests():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT subject, date, description FROM tests ORDER BY date")
        return cur.fetchall()
