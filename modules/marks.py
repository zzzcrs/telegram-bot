import sqlite3

DB_PATH = "bot_db.sqlite"

def init():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            mark INTEGER
        )
        """)
        conn.commit()

def add_mark(user_id, subject, mark):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO marks (user_id, subject, mark) VALUES (?, ?, ?)", (user_id, subject, mark))
        conn.commit()

def get_marks(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT subject, mark FROM marks WHERE user_id=?", (user_id,))
        return cur.fetchall()

def get_avg(user_id, subject):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT mark FROM marks WHERE user_id=? AND subject=?", (user_id, subject))
        rows = cur.fetchall()
        if not rows:
            return 0
        return sum(r[0] for r in rows)/len(rows)

def clear_marks(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM marks WHERE user_id=?", (user_id,))
        conn.commit()
