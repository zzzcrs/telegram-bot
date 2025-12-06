import sqlite3
from datetime import datetime
from modules.tests import get_tests

DB_PATH = "bot_db.sqlite"

def tests_for_today():
    today = datetime.now().date().isoformat()
    rows = get_tests()
    return [r for r in rows if r[1] == today]

async def daily_morning_job(context):
    bot = context.bot

    # Получаем всех пользователей
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users")
        users = [r[0] for r in cur.fetchall()]

    # Формируем сообщение
    msg = "Доброе утро! Вот план на сегодня:\n\n"

    tests = tests_for_today()
    if tests:
        msg += "🧪 Сегодня контрольные:\n"
        for subj, date, desc in tests:
            msg += f"• {subj}: {desc}\n"

    # Домашка на сегодня
    today_str = datetime.now().date().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT subject, text FROM homework WHERE due_date = ?", (today_str,))
        hws = cur.fetchall()

    if hws:
        msg += "\n📚 Сегодня сдавать:\n"
        for subj, text in hws:
            msg += f"• {subj}: {text}\n"

    # Отправка всем пользователям
    for u in users:
        try:
            await bot.send_message(u, msg)
        except Exception:
            pass
