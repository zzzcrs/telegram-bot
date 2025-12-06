# utils/scheduler.py
from datetime import datetime
from modules.tests import get_tests
from db import connect

def tests_for_today():
    today = datetime.now().date().isoformat()
    rows = get_tests()
    # rows: (subject, test_date, desc)
    return [r for r in rows if r[1] == today]

async def daily_morning_job(context):
    # runs every morning via job_queue
    bot = context.bot
    # send schedule + today's hw/tests to all users
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    users = [r[0] for r in cur.fetchall()]
    conn.close()

    # build message
    msg = "Доброе утро! Вот план на сегодня:\n\n"
    # schedule part will be fetched per user if needed; keep generic
    tests = tests_for_today()
    if tests:
        msg += "🧪 Сегодня контрольные:\n"
        for subj, date, desc in tests:
            msg += f"• {subj}: {desc}\n"
    # homework due today
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT subject, text FROM homework WHERE due_date = ?", (datetime.now().date().isoformat(),))
    hws = cur.fetchall()
    conn.close()
    if hws:
        msg += "\n📚 Сегодня сдавать:\n"
        for subj, text in hws:
            msg += f"• {subj}: {text}\n"

    for u in users:
        try:
            await bot.send_message(u, msg)
        except Exception:
            pass
