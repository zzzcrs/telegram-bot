import re
from datetime import datetime, timedelta

from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton,
    InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

from db import init_db, add_user, log_action, connect
from modules.announce import add_announce as db_add_announce, get_all_announcements as db_get_all_announcements
from modules.homework import add_hw as db_add_hw, get_hw as db_get_hw
from modules.marks import add_mark as db_add_mark, get_marks as db_get_marks, get_avg as db_get_avg, \
    clear_marks as db_clear_marks
from modules.schedule import get_day_schedule, add_schedule_entry
from modules.tests import add_test as db_add_test, get_tests as db_get_tests
from utils.excel_import import import_marks_from_excel
from utils.export_excel import export_excel
from utils.scheduler import daily_morning_job

TOKEN = '8292924282:AAFXPnq5d8cLviX4ZNQuyRgm3y-RRCLN2ZM'  # Замените на ваш токен!

# ---------------- Reply keyboard ----------------
menu_keyboard = [
    ["📅 Сегодня", "📅 Завтра"],
    ["📂 Домашка", "🧪 Контрольные"],
    ["⭐ Мои оценки", "➕ Добавить"],
    ["📢 Объявления", "⚙️ Экспорт/Очистка"],
    ["❓ Помощь"]
]
markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)


# ---------------- Helpers ----------------
def parse_date_like(text: str):
    text = text.strip().lower()
    if text in ("сегодня", "today", "сейчас"):
        return datetime.now().date().isoformat()
    if text in ("завтра", "tomorrow"):
        return (datetime.now().date() + timedelta(days=1)).isoformat()
    if text in ("послезавтра", "day after tomorrow"):
        return (datetime.now().date() + timedelta(days=2)).isoformat()

    # Пробуем разные форматы дат
    date_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d.%m", "%d/%m"]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(text, fmt)
            if fmt in ["%d.%m", "%d/%m"]:  # Только день и месяц
                dt = dt.replace(year=datetime.now().year)
            return dt.date().isoformat()
        except:
            continue
    return None


# ---------------- Commands ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    await update.message.reply_text(
        "Привет! Я школьный помощник. Выбери действие или напиши команду.",
        reply_markup=markup
    )
    log_action(user.id, "start")


async def help_cmd(update: Update, context):
    await update.message.reply_text(
        "📚 *Команды:*\n"
        "• /start - начать работу\n"
        "• /today - расписание на сегодня\n"
        "• /tomorrow - расписание на завтра\n"
        "• /hw [предмет] - домашние задания\n"
        "• /add_hw <предмет> <текст> - добавить домашку\n"
        "• /add_mark <предмет> <оценка> - добавить оценку\n"
        "• /my_marks - мои оценки\n"
        "• /add_schedule <день 0-6> <номер> <предмет> <кабинет> - добавить расписание\n"
        "• /announce <текст> - добавить объявление (для админов)\n"
        "• /export_excel - выгрузить данные в Excel\n"
        "• /import_excel <файл> - импорт оценок из Excel\n"
        "• /export - выгрузить в txt\n\n"

        "🎛 *Кнопки меню:*\n"
        "• 📅 Сегодня/Завтра - расписание\n"
        "• 📂 Домашка - домашние задания\n"
        "• 🧪 Контрольные - тесты и контрольные\n"
        "• ⭐ Мои оценки - ваши оценки\n"
        "• ➕ Добавить - добавить данные\n"
        "• 📢 Объявления - посмотреть объявления\n"
        "• ⚙️ Экспорт/Очистка - управление данными\n"
        "• ❓ Помощь",

        parse_mode='Markdown'
    )


# ---------------- Расписание ----------------
async def add_schedule(update: Update, context):
    """Добавление расписания через команду"""
    if not context.args or len(context.args) < 4:
        await update.message.reply_text(
            "📝 *Добавление расписания*\n\n"
            "Использование: `/add_schedule <день_недели> <номер_урока> <предмет> <кабинет>`\n\n"
            "Примеры:\n"
            "`/add_schedule 0 1 Математика 301` - Понедельник, 1 урок\n"
            "`/add_schedule 1 2 Физика 205` - Вторник, 2 урок\n\n"
            "Дни недели: 0-Понедельник, 1-Вторник, ..., 6-Воскресенье",
            parse_mode='Markdown'
        )
        return

    try:
        weekday = int(context.args[0])
        lesson_num = int(context.args[1])
        subject = context.args[2]
        room = context.args[3]

        add_schedule_entry(weekday, lesson_num, subject, room)
        await update.message.reply_text(f"✅ Расписание добавлено!\n"
                                        f"День: {weekday}, Урок: {lesson_num}\n"
                                        f"Предмет: {subject}, Кабинет: {room}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


# ---------------- Объявления ----------------
async def announce(update: Update, context):
    """Добавить объявление для всех"""
    if not context.args:
        await update.message.reply_text("Использование: /announce <текст>")
        return

    text = " ".join(context.args)
    db_add_announce(text)

    # Рассылка всем пользователям
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    users = [row[0] for row in cur.fetchall()]
    conn.close()

    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(
                user_id,
                f"📢 *НОВОЕ ОБЪЯВЛЕНИЕ*\n\n{text}\n\n_Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}_",
                parse_mode='Markdown'
            )
            count += 1
        except Exception as e:
            print(f"Не удалось отправить объявление пользователю {user_id}: {e}")

    await update.message.reply_text(f"✅ Объявление отправлено {count} пользователям!")


# ---------------- Inline Add Menu ----------------
def add_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("📝 Добавить домашку", callback_data="add_hw")],
        [InlineKeyboardButton("⭐ Добавить оценку", callback_data="add_mark")],
        [InlineKeyboardButton("🧪 Добавить контрольную", callback_data="add_test")],
        [InlineKeyboardButton("📅 Добавить расписание", callback_data="add_schedule_dialog")],
    ]
    return InlineKeyboardMarkup(buttons)


async def add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Что добавить?", reply_markup=add_menu_keyboard())


# ---------------- Show schedule & homework ----------------
async def show_today(update: Update, context):
    weekday = datetime.now().weekday()
    lessons = get_day_schedule(weekday)
    if not lessons:
        await update.message.reply_text("📭 Сегодня занятий нет.")
        return

    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    msg = f"📅 *Расписание на сегодня ({day_names[weekday]}):*\n\n"
    for num, subj, room in lessons:
        msg += f"• {num}. *{subj}* — каб. {room}\n"

    # Показываем также домашку на сегодня
    uid = update.message.from_user.id
    today_date = datetime.now().date().isoformat()
    hws = db_get_hw(user_id=uid)
    hws_today = [f"📚 {s}: {t}" for s, t, due, _ in hws if due == today_date]

    if hws_today:
        msg += "\n📌 *На сегодня:*\n" + "\n".join(hws_today)

    await update.message.reply_text(msg, parse_mode='Markdown')


async def show_tomorrow(update: Update, context):
    weekday = (datetime.now().weekday() + 1) % 7
    lessons = get_day_schedule(weekday)
    if not lessons:
        await update.message.reply_text("📭 Завтра занятий нет.")
        return

    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    msg = f"📅 *Расписание на завтра ({day_names[weekday]}):*\n\n"
    for num, subj, room in lessons:
        msg += f"• {num}. *{subj}* — каб. {room}\n"
    await update.message.reply_text(msg, parse_mode='Markdown')


async def show_hw_cmd(update: Update, context):
    uid = update.message.from_user.id
    subject = context.args[0].lower() if context.args else None
    rows = db_get_hw(subject=subject, user_id=uid)

    if not rows:
        await update.message.reply_text("✅ Домашки нет.")
        return

    # Группируем по предметам
    hw_by_subject = {}
    for subj, text, due, date_added in rows:
        if subj not in hw_by_subject:
            hw_by_subject[subj] = []
        due_display = due if due else "без срока"
        hw_by_subject[subj].append(f"  • {text} (до {due_display})")

    msg = "📚 *Домашние задания:*\n\n"
    for subject, assignments in hw_by_subject.items():
        msg += f"*{subject.capitalize()}*:\n"
        msg += "\n".join(assignments) + "\n\n"

    await update.message.reply_text(msg, parse_mode='Markdown')


# ---------------- User dialog state ----------------
USER_STATE = {}


# ---------------- Callback query handler ----------------
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add_hw":
        USER_STATE[user_id] = {"flow": "add_hw", "step": 1}
        await query.edit_message_text("📝 *Добавление домашки*\n\nУкажи предмет (например, математика):",
                                      parse_mode='Markdown')
    elif query.data == "add_mark":
        USER_STATE[user_id] = {"flow": "add_mark", "step": 1}
        await query.edit_message_text("⭐ *Добавление оценки*\n\nУкажи предмет:", parse_mode='Markdown')
    elif query.data == "add_test":
        USER_STATE[user_id] = {"flow": "add_test", "step": 1}
        await query.edit_message_text("🧪 *Добавление контрольной*\n\nУкажи предмет:", parse_mode='Markdown')
    elif query.data == "add_schedule_dialog":
        USER_STATE[user_id] = {"flow": "add_schedule_dialog", "step": 1}
        await query.edit_message_text(
            "📅 *Добавление расписания*\n\n"
            "Укажи день недели (0-6):\n"
            "0-Понедельник, 1-Вторник, ..., 6-Воскресенье",
            parse_mode='Markdown'
        )
    elif query.data == "export":
        await export_cmd(update, context)
    elif query.data == "export_excel":
        await export_excel(update, context)
    elif query.data == "clear_marks":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, удалить все", callback_data="confirm_clear")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ])
        await query.edit_message_text(
            "⚠️ *Внимание!*\n\nУверен(а)? Это действие удалит ВСЕ твои оценки без возможности восстановления.",
            reply_markup=kb, parse_mode='Markdown')
    elif query.data == "confirm_clear":
        db_clear_marks(user_id)
        await query.edit_message_text("✅ Все оценки удалены.")
    elif query.data == "cancel":
        await query.edit_message_text("❌ Действие отменено.")
    elif query.data == "show_announcements":
        announcements = db_get_all_announcements()
        if not announcements:
            await query.edit_message_text("📭 Объявлений нет.")
            return
        msg = "📢 *Последние объявления:*\n\n"
        for text, date_created in announcements[:5]:  # Последние 5
            msg += f"• {text}\n  _{date_created[:10]}_\n\n"
        await query.edit_message_text(msg, parse_mode='Markdown')


# ---------------- Dialog text handler ----------------
async def dialog_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    # --------- ReplyKeyboard buttons ----------
    if text == "📅 Сегодня":
        await show_today(update, context)
        return
    elif text == "📅 Завтра":
        await show_tomorrow(update, context)
        return
    elif text == "📂 Домашка":
        await show_hw_cmd(update, context)
        return
    elif text == "🧪 Контрольные":
        tests = db_get_tests()
        if not tests:
            await update.message.reply_text("✅ Контрольных нет.")
            return
        msg = "🧪 *Контрольные и тесты:*\n\n"
        for subject, test_date, description in tests:
            msg += f"• *{subject}* — {test_date}\n  {description}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    elif text == "⭐ Мои оценки":
        rows = db_get_marks(uid)
        if not rows:
            await update.message.reply_text("📭 Оценок нет.")
            return

        msg = "⭐ *Мои оценки:*\n\n"
        for subject, marks_str in rows:
            marks = marks_str.split() if isinstance(marks_str, str) else marks_str
            avg_subj = db_get_avg(uid, subject)
            msg += f"*{subject.capitalize()}*: {' '.join(marks)}"
            if avg_subj:
                msg += f" (среднее: {float(avg_subj):.2f})"
            msg += "\n"

        avg_all = db_get_avg(uid)
        if avg_all:
            msg += f"\n📊 *Общий средний балл:* {float(avg_all):.2f}"

        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    elif text == "➕ Добавить":
        await add_menu(update, context)
        return
    elif text == "📢 Объявления":
        announcements = db_get_all_announcements()
        if not announcements:
            await update.message.reply_text("📭 Объявлений нет.")
            return
        msg = "📢 *Последние объявления:*\n\n"
        for text, date_created in announcements[:10]:  # Последние 10
            date_display = datetime.strptime(date_created, "%Y-%m-%dT%H:%M:%S.%f").strftime("%d.%m.%Y %H:%M")
            msg += f"• {text}\n  _{date_display}_\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    elif text == "❓ Помощь" or text == "Помощь" or text == "help" or text == "Help":
        await help_cmd(update, context)
        return

    elif text == "⚙️ Экспорт/Очистка":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Экспорт в TXT", callback_data="export")],
            [InlineKeyboardButton("📊 Экспорт в Excel", callback_data="export_excel")],
            [InlineKeyboardButton("🗑️ Очистить оценки", callback_data="clear_marks")],
            [InlineKeyboardButton("📢 Показать объявления", callback_data="show_announcements")]
        ])
        await update.message.reply_text("⚙️ *Управление данными:*", reply_markup=kb, parse_mode='Markdown')
        return

    # --------- Dialog flows ----------
    state = USER_STATE.get(uid)
    if state:
        flow = state["flow"]
        step = state["step"]

        if flow == "add_hw":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text(
                    "📝 Укажи дату сдачи (YYYY-MM-DD, DD.MM.YYYY или 'завтра', 'послезавтра'):\n\n_Можно пропустить, отправив '-'_")
                return
            elif step == 2:
                if text.strip() in ("-", "нет", "без срока"):
                    state["due_date"] = None
                else:
                    maybe_date = parse_date_like(text)
                    if not maybe_date:
                        await update.message.reply_text(
                            "❌ Неверный формат даты. Попробуй еще раз (например, 15.12.2024 или 'завтра'):")
                        return
                    state["due_date"] = maybe_date
                state["step"] = 3
                await update.message.reply_text("📝 Теперь напиши текст задания:")
                return
            elif step == 3:
                state["text"] = text
                db_add_hw(state["subject"], state["text"], uid, state.get("due_date"))
                del USER_STATE[uid]

                due_display = state.get("due_date") if state.get("due_date") else "без срока"
                await update.message.reply_text(
                    f"✅ *Домашка добавлена!*\n\n"
                    f"*Предмет:* {state['subject']}\n"
                    f"*Задание:* {state['text']}\n"
                    f"*Срок:* {due_display}",
                    parse_mode='Markdown'
                )
                return

        elif flow == "add_mark":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("⭐ Укажи оценку (1-5, можно несколько через пробел):")
                return
            elif step == 2:
                marks = text.strip().split()
                added = 0
                errors = []

                for mark_str in marks:
                    try:
                        mark = int(mark_str)
                        if 1 <= mark <= 5:
                            db_add_mark(uid, state["subject"], mark)
                            added += 1
                        else:
                            errors.append(f"Оценка {mark} вне диапазона 1-5")
                    except ValueError:
                        errors.append(f"'{mark_str}' - не число")

                del USER_STATE[uid]

                msg = f"✅ Добавлено {added} оценок по предмету *{state['subject']}*"
                if errors:
                    msg += f"\n❌ Ошибки: {', '.join(errors[:3])}"
                await update.message.reply_text(msg, parse_mode='Markdown')
                return

        elif flow == "add_test":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("🧪 Укажи дату теста (YYYY-MM-DD или 'завтра', 'послезавтра'):")
                return
            elif step == 2:
                dd = parse_date_like(text)
                if not dd:
                    await update.message.reply_text("❌ Неверная дата. Попробуй еще раз (YYYY-MM-DD или 'завтра'):")
                    return
                state["date"] = dd
                state["step"] = 3
                await update.message.reply_text("🧪 Краткое описание теста (что будет на тесте):")
                return
            elif step == 3:
                desc = text
                db_add_test(state["subject"], state["date"], desc)
                del USER_STATE[uid]
                await update.message.reply_text(
                    f"✅ *Контрольная добавлена!*\n\n"
                    f"*Предмет:* {state['subject']}\n"
                    f"*Дата:* {state['date']}\n"
                    f"*Описание:* {desc}",
                    parse_mode='Markdown'
                )
                return

        elif flow == "add_schedule_dialog":
            if step == 1:
                try:
                    weekday = int(text)
                    if weekday < 0 or weekday > 6:
                        raise ValueError()
                    state["weekday"] = weekday
                    state["step"] = 2

                    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                    await update.message.reply_text(
                        f"📅 *День недели:* {day_names[weekday]}\n\n"
                        f"Укажи номер урока (1, 2, 3...):"
                        , parse_mode='Markdown')
                except:
                    await update.message.reply_text("❌ Неверный день недели. Введи число от 0 до 6:")
                return
            elif step == 2:
                try:
                    lesson_num = int(text)
                    state["lesson_num"] = lesson_num
                    state["step"] = 3
                    await update.message.reply_text("📝 Укажи название предмета:")
                except:
                    await update.message.reply_text("❌ Неверный номер урока. Введи число:")
                return
            elif step == 3:
                state["subject"] = text
                state["step"] = 4
                await update.message.reply_text("🚪 Укажи номер кабинета:")
                return
            elif step == 4:
                state["room"] = text
                # Сохраняем расписание
                add_schedule_entry(state["weekday"], state["lesson_num"], state["subject"], state["room"])
                del USER_STATE[uid]

                day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                await update.message.reply_text(
                    f"✅ *Расписание добавлено!*\n\n"
                    f"*День:* {day_names[state['weekday']]}\n"
                    f"*Урок:* {state['lesson_num']}\n"
                    f"*Предмет:* {state['subject']}\n"
                    f"*Кабинет:* {state['room']}",
                    parse_mode='Markdown'
                )
                return

        return

    # --------- Simple NLU fallback ----------
    await simple_nlu_handler(update, context)


# ---------------- Simple NLU ----------------
async def simple_nlu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    uid = update.message.from_user.id

    # add mark quick
    m = re.search(r"(?:добавь|поставь|оценка)\s*(?:по\s*)?(?P<subject>\w+)\s+(?P<mark>[1-5])", text)
    if m:
        subj = m.group("subject")
        mark = int(m.group("mark"))
        db_add_mark(uid, subj, mark)
        await update.message.reply_text(f"✅ Оценка {mark} по {subj} добавлена.")
        return

    # add hw quick
    m = re.match(r"(?:добавь|добавить)\s+домашк(?:у|а)\s+(?:по\s+)?(?P<subject>\w+)\s+(?P<text>.+)", text)
    if m:
        subj = m.group("subject")
        body = m.group("text")
        db_add_hw(subj, body, uid, None)
        await update.message.reply_text(f"✅ Домашка по {subj} добавлена:\n{body}")
        return



# ---------------- Export ----------------
async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lines = []
    lines.append("=" * 40)
    lines.append("        ШКОЛЬНЫЙ ПОМОЩНИК")
    lines.append(f"      Экспорт от {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    lines.append("=" * 40)

    lines.append("\n=== ДОМАШНИЕ ЗАДАНИЯ ===")
    hw = db_get_hw(user_id=uid)
    if hw:
        for s, txt, due, added in hw:
            due_display = due if due else "без срока"
            lines.append(f"• {s}: {txt} (срок: {due_display})")
    else:
        lines.append("Домашних заданий нет")

    lines.append("\n=== КОНТРОЛЬНЫЕ И ТЕСТЫ ===")
    tests = db_get_tests()
    if tests:
        for s, date, desc in tests:
            lines.append(f"• {s}: {desc} (дата: {date})")
    else:
        lines.append("Контрольных нет")

    lines.append("\n=== ОЦЕНКИ ===")
    marks = db_get_marks(uid)
    if marks:
        for s, m in marks:
            lines.append(f"• {s}: {m}")
        avg = db_get_avg(uid)
        if avg:
            lines.append(f"\nСредний балл: {float(avg):.2f}")
    else:
        lines.append("Оценок нет")

    lines.append("\n=== ОБЪЯВЛЕНИЯ ===")
    announcements = db_get_all_announcements()
    if announcements:
        for text, date in announcements[:5]:
            lines.append(f"• {text} ({date[:10]})")
    else:
        lines.append("Объявлений нет")

    lines.append("\n" + "=" * 40)
    content = "\n".join(lines)

    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    await update.message.reply_document(
        document=InputFile(filename),
        caption="📁 Экспорт данных завершен!"
    )


async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /export_excel"""
    # Эта функция должна быть импортирована из utils.export_excel
    from utils.export_excel import export_excel as export_excel_func
    await export_excel_func(update, context)


# ---------------- Import from Excel ----------------
async def import_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Импорт оценок из Excel файла"""
    if update.message.document:
        # Обработка загруженного файла
        await import_marks_from_excel(update, context)
    elif context.args:
        # Обработка указанного пути
        await import_marks_from_excel(update, context)
    else:
        await update.message.reply_text(
            "📤 *Как импортировать оценки из Excel:*\n\n"
            "1. *Отправьте файл:* Просто пришлите Excel файл (.xlsx) в чат\n"
            "2. *Через команду:* `/import_excel путь_к_файлу`\n\n"
            "Формат файла:\n"
            "• Столбец A: название предмета\n"
            "• Столбец B: оценка (1-5)\n\n"
            "*Пример файла:*\n"
            "| Предмет   | Оценка |\n"
            "|-----------|--------|\n"
            "| Математика| 5      |\n"
            "| Физика    | 4      |",
            parse_mode='Markdown'
        )


# ---------------- Setup & Run ----------------
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", show_today))
    app.add_handler(CommandHandler("tomorrow", show_tomorrow))
    app.add_handler(CommandHandler("hw", show_hw_cmd))
    app.add_handler(CommandHandler("add", add_menu))
    app.add_handler(CommandHandler("export", export_cmd))
    app.add_handler(CommandHandler("export_excel", export_excel))
    app.add_handler(CommandHandler("import_excel", import_excel))
    app.add_handler(CommandHandler("add_schedule", add_schedule))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("my_marks", lambda u, c: dialog_text_handler(u, c)))  # Для команды
    app.add_error_handler(error_handler)

    # callback queries
    app.add_handler(CallbackQueryHandler(on_callback))

    # messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dialog_text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # morning job at 08:00
    try:
        app.job_queue.run_daily(daily_morning_job, time=datetime.strptime("08:00", "%H:%M").time())
        print("✅ Утренние уведомления включены (08:00)")
    except Exception as e:
        print(f"⚠️ Не удалось настроить утренние уведомления: {e}")

    print("🤖 Бот запущен...")
    app.run_polling()


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отправленных файлов"""
    document = update.message.document

    # Проверяем, что это Excel файл
    if document.file_name.endswith(('.xlsx', '.xls')):
        await update.message.reply_text("📤 Получен Excel файл. Импортирую оценки...")
        await import_marks_from_excel(update, context)
    else:
        await update.message.reply_text("❌ Пожалуйста, отправьте Excel файл (.xlsx)")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"⚠️ Ошибка: {context.error}")
    try:
        raise context.error
    except Exception as e:
        print(f"Детали ошибки: {e}")


if __name__ == "__main__":
    main()
