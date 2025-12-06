import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "school.db"

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS schedule(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weekday INTEGER,
        lesson_number INTEGER,
        subject TEXT,
        room TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS homework(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        text TEXT,
        due_date TEXT,
        date_added TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        test_date TEXT,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        mark INTEGER,
        date_added TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS announcements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        date_created TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        ts TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Создаем индексы для ускорения работы
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hw_user ON homework(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hw_subject ON homework(subject)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_marks_user ON marks(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_marks_subject ON marks(subject)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_schedule_weekday ON schedule(weekday)")

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def add_user(user_id: int, username: Optional[str]):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?,?)", (user_id, username))
    conn.commit()
    conn.close()

def log_action(user_id, action):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (user_id, action, ts) VALUES (?, ?, ?)",
                (user_id, action, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_users():
    """Получить всех пользователей"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows