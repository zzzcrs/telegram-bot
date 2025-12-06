from db import connect
from datetime import datetime


def add_hw(subject: str, text: str, user_id: int, due_date: str = None):
    """Добавить домашнее задание"""
    conn = connect()
    cur = conn.cursor()

    # Вставляем новое задание (разрешаем несколько по одному предмету)
    cur.execute(
        "INSERT INTO homework (user_id, subject, text, due_date, date_added) VALUES (?, ?, ?, ?, ?)",
        (user_id, subject, text, due_date, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_hw(subject: str = None, user_id: int = None):
    """Получить домашние задания"""
    conn = connect()
    cur = conn.cursor()

    query = "SELECT subject, text, due_date, date_added FROM homework WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id=?"
        params.append(user_id)

    if subject:
        query += " AND subject=?"
        params.append(subject)

    query += " ORDER BY due_date, date_added"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return rows


def delete_hw(subject: str, user_id: int):
    """Удалить домашнее задание"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM homework WHERE user_id=? AND subject=?", (user_id, subject))
    conn.commit()
    conn.close()


def get_hw_by_date(user_id: int, date: str):
    """Получить домашку на конкретную дату"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT subject, text FROM homework 
        WHERE user_id=? AND due_date=? 
        ORDER BY subject
    """, (user_id, date))
    rows = cur.fetchall()
    conn.close()
    return rows