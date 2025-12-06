from db import connect
from datetime import datetime


def add_mark(user_id: int, subject: str, mark: int):
    """Добавить оценку"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO marks (user_id, subject, mark, date_added) VALUES (?, ?, ?, ?)",
                (user_id, subject, mark, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_marks(user_id: int):
    """Получить оценки пользователя, сгруппированные по предметам"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT subject, mark FROM marks WHERE user_id=? ORDER BY subject, date_added", (user_id,))
    rows = cur.fetchall()
    conn.close()

    # Сгруппировать по предмету
    grouped = {}
    for subj, mark in rows:
        if subj not in grouped:
            grouped[subj] = []
        grouped[subj].append(str(mark))

    # Возвращаем в формате (предмет, строку оценок через пробел)
    return [(subj, " ".join(marks)) for subj, marks in grouped.items()]


def get_avg(user_id: int, subject: str = None):
    """Получить средний балл"""
    conn = connect()
    cur = conn.cursor()

    if subject:
        cur.execute("SELECT AVG(mark) FROM marks WHERE user_id=? AND subject=?", (user_id, subject))
    else:
        cur.execute("SELECT AVG(mark) FROM marks WHERE user_id=?", (user_id,))

    result = cur.fetchone()[0]
    conn.close()
    return result


def clear_marks(user_id: int):
    """Очистить все оценки пользователя"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM marks WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_marks_detailed(user_id: int, subject: str = None):
    """Получить оценки с деталями (датами)"""
    conn = connect()
    cur = conn.cursor()

    if subject:
        cur.execute("SELECT mark, date_added FROM marks WHERE user_id=? AND subject=? ORDER BY date_added",
                    (user_id, subject))
    else:
        cur.execute("SELECT subject, mark, date_added FROM marks WHERE user_id=? ORDER BY subject, date_added",
                    (user_id,))

    rows = cur.fetchall()
    conn.close()
    return rows