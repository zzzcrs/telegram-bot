from modules.tests import get_tests
from modules.schedule import get_day_schedule
from modules.homework import get_hw_by_date
from db import get_all_users
from datetime import datetime, timedelta


async def daily_morning_job(context):
    """Ежедневное утреннее уведомление"""
    bot = context.bot
    users = get_all_users()

    today = datetime.now().date().isoformat()
    weekday = datetime.now().weekday()
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    # Получаем общие данные
    lessons = get_day_schedule(weekday)
    tests = get_tests(date_from=today, date_to=today)

    for user_id, username in users:
        try:
            msg = f"🌅 *Доброе утро!*\n"
            msg += f"Сегодня *{day_names[weekday]}, {today}*\n\n"

            # Расписание
            if lessons:
                msg += "📅 *Расписание на сегодня:*\n"
                for num, subj, room in lessons:
                    msg += f"• {num}. {subj} — каб. {room}\n"
                msg += "\n"

            # Домашка на сегодня
            hw_today = get_hw_by_date(user_id, today)
            if hw_today:
                msg += "📚 *Домашка на сегодня:*\n"
                for subj, text in hw_today:
                    msg += f"• {subj}: {text}\n"
                msg += "\n"

            # Контрольные сегодня
            if tests:
                msg += "🧪 *Контрольные сегодня:*\n"
                for subj, date, desc in tests:
                    msg += f"• {subj}: {desc}\n"
                msg += "\n"

            # Если ничего нет
            if len(msg.split('\n')) <= 5:
                msg += "✅ Сегодня ничего не запланировано. Хорошего дня!"

            await bot.send_message(user_id, msg, parse_mode='Markdown')

        except Exception as e:
            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")