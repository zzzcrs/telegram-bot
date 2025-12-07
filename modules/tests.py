from db import connect


def add_test(subject: str, test_date: str, desc: str):
    """Добавить контрольную/тест"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO tests (subject, test_date, description) VALUES (?, ?, ?)",
                (subject, test_date, desc))
    conn.commit()
    conn.close()


def get_tests(subject: str = None, date_from: str = None, date_to: str = None):
    """Получить контрольные/тесты"""
    conn = connect()
    cur = conn.cursor()

    query = "SELECT subject, test_date, description FROM tests WHERE 1=1"
    params = []

    if subject:
        query += " AND subject=?"
        params.append(subject)

    if date_from:
        query += " AND test_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND test_date <= ?"
        params.append(date_to)

    query += " ORDER BY test_date"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_test(test_id: int = None, subject: str = None):
    """Удалить контрольную"""
    conn = connect()
    cur = conn.cursor()

    if test_id:
        cur.execute("DELETE FROM tests WHERE id=?", (test_id,))
    elif subject:
        cur.execute("DELETE FROM tests WHERE subject=?", (subject,))

    conn.commit()
    conn.close()
