import re
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from db import init_db, add_user, log_action
from modules.schedule import get_day_schedule, get_week_schedule, add_schedule_entry
from modules.homework import add_hw as db_add_hw, get_hw as db_get_hw, delete_hw as db_delete_hw
from modules.tests import add_test as db_add_test, get_tests as db_get_tests
from modules.marks import add_mark as db_add_mark, get_marks as db_get_marks, get_avg as db_get_avg, clear_marks as db_clear_marks
from modules.announce import add_announce as db_add_announce, get_all_announcements
from utils.scheduler import daily_morning_job

TOKEN = '8292924282:AAFXPnq5d8cLviX4ZNQuyRgm3y-RRCLN2ZM'

menu_keyboard = [
    ["📅 Сегодня", "📅 Завтра"],
    ["📂 Домашка", "🧪 Контрольные"],
    ["⭐ Мои оценки", "➕ Добавить", "⚙️ Экспорт/Очистка"]
]
markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

USER_STATE = {}

def parse_date_like(text: str):
    text = text.strip().lower()
    if text in ("сегодня", "today"):
        return datetime.now().date().isoformat()
    if text in ("завтра", "tomorrow"):
        return (datetime.now().date() + timedelta(days=1)).isoformat()
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except:
        return None

# ---------------- Commands ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    await update.message.reply_text("Привет! Я школьный помощник. Выбери действие или напиши команду.", reply_markup=markup)
    log_action(user.id, "start")

async def help_cmd(update: Update, context):
    await update.message.reply_text(
        "Команды:\n"
        "/today - расписание на сегодня\n"
        "/tomorrow - расписание на завтра\n"
        "/hw [предмет] - показать домашку\n"
        "/add_hw <предмет> <текст> - добавить домашку\n"
        "/add_mark <предмет> <оценка> - добавить оценку\n"
        "/my_marks - показать оценки\n"
        "/export - выгрузить данные в txt\n"
    )

# ---------------- Inline Add Menu ----------------
def add_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("Добавить домашку", callback_data="add_hw")],
        [InlineKeyboardButton("Добавить оценку", callback_data="add_mark")],
        [InlineKeyboardButton("Добавить контрольную", callback_data="add_test")],
    ]
    return InlineKeyboardMarkup(buttons)

async def add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Что добавить?", reply_markup=add_menu_keyboard())

# ---------------- Show schedule & homework ----------------
async def show_today(update: Update, context):
    weekday = datetime.now().weekday()
    lessons = get_day_schedule(weekday)
    if not lessons:
        await update.message.reply_text("Сегодня занятий нет.")
        return
    msg = "📅 Расписание на сегодня:\n"
    for num, subj, room in lessons:
        msg += f"{num}. {subj} — {room}\n"
    await update.message.reply_text(msg)

async def show_tomorrow(update: Update, context):
    weekday = (datetime.now().weekday() + 1) % 7
    lessons = get_day_schedule(weekday)
    if not lessons:
        await update.message.reply_text("Завтра занятий нет.")
        return
    msg = "📅 Расписание на завтра:\n"
    for num, subj, room in lessons:
        msg += f"{num}. {subj} — {room}\n"
    await update.message.reply_text(msg)

async def show_hw_cmd(update: Update, context):
    subject = context.args[0].lower() if context.args else None
    rows = db_get_hw(subject)
    if not rows:
        await update.message.reply_text("Домашки нет.")
        return
    msg = "📚 Домашние задания:\n"
    for subj, text, due_date, added in rows:
        msg += f"• {subj} — {text}\n"
    await update.message.reply_text(msg)

async def show_marks(update: Update, context):
    uid = update.message.from_user.id
    rows = db_get_marks(uid)
    if not rows:
        await update.message.reply_text("Оценок нет.")
        return
    msg = "⭐ Мои оценки:\n"
    subjects = {}
    for subj, mark in rows:
        subjects.setdefault(subj, []).append(str(mark))
    for s, m_list in subjects.items():
        avg = db_get_avg(update.message.from_user.id, s)
        msg += f"{s}: {' '.join(m_list)} (ср. {avg:.2f})\n"
    # общий средний
    total_avg = sum([sum(map(int, marks)) for marks in subjects.values()]) / sum([len(marks) for marks in subjects.values()])
    msg += f"\nОбщий средний: {total_avg:.2f}"
    await update.message.reply_text(msg)

# ---------------- Callback ----------------
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "add_hw":
        USER_STATE[user_id] = {"flow": "add_hw", "step": 1}
        await query.edit_message_text("📝 Добавление домашки.\nУкажи предмет:")
    elif query.data == "add_mark":
        USER_STATE[user_id] = {"flow": "add_mark", "step": 1}
        await query.edit_message_text("⭐ Добавление оценки.\nУкажи предмет:")
    elif query.data == "add_test":
        USER_STATE[user_id] = {"flow": "add_test", "step": 1}
        await query.edit_message_text("🧪 Добавление контрольной.\nУкажи предмет:")

# ---------------- Dialog text ----------------
async def dialog_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    # кнопки
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
        msg = "🧪 Контрольные:\n" + "\n".join([f"{s} — {d} — {desc}" for s,d,desc in tests]) if tests else "Контрольных нет."
        await update.message.reply_text(msg)
        return
    elif text == "⭐ Мои оценки":
        await show_marks(update, context)
        return
    elif text == "➕ Добавить":
        await add_menu(update, context)
        return

    state = USER_STATE.get(uid)
    if state:
        flow = state["flow"]
        step = state["step"]
        if flow == "add_hw":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("Теперь напиши текст задания:")
            elif step == 2:
                state["text"] = text
                db_add_hw(state["subject"], state["text"])
                del USER_STATE[uid]
                await update.message.reply_text(f"Добавлено: {state['subject']} — {state['text']}")
        elif flow == "add_mark":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("Укажи оценку (1-5):")
            elif step == 2:
                try:
                    mark = int(text)
                    if mark < 1 or mark > 5:
                        raise ValueError()
                except:
                    await update.message.reply_text("Ошибка: укажи число от 1 до 5.")
                    return
                db_add_mark(uid, state["subject"], mark)
                del USER_STATE[uid]
                await update.message.reply_text(f"Оценка {mark} по {state['subject']} добавлена.")
        elif flow == "add_test":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("Укажи дату теста (YYYY-MM-DD или 'завтра'):")
            elif step == 2:
                dd = parse_date_like(text)
                if not dd:
                    await update.message.reply_text("Неверная дата. Попробуй ещё раз:")
                    return
                state["date"] = dd
                state["step"] = 3
                await update.message.reply_text("Краткое описание теста:")
            elif step == 3:
                desc = text
                db_add_test(state["subject"], state["date"], desc)
                del USER_STATE[uid]
                await update.message.reply_text(f"Контрольная по {state['subject']} запланирована на {state['date']}.")

    # простая NLU
    await simple_nlu_handler(update, context)

async def simple_nlu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    m = re.search(r"(?:добавь|поставь)?\s*(?:оценку\s*)?(?:по\s*)?(?P<subject>\w+)\s*(?P<mark>[1-5])$", text)
    if m:
        subj = m.group("subject")
        mark = int(m.group("mark"))
        db_add_mark(update.message.from_user.id, subj, mark)
        await update.message.reply_text(f"Оценка {mark} по {subj} добавлена.")
        return
    m = re.match(r"(?:добавь|поставь)\s+домашк(?:у|а)\s+(?:по\s+)?(?P<subject>\w+)\s+(?P<text>.+)", text)
    if m:
        subj = m.group("subject")
        body = m.group("text")
        db_add_hw(subj, body)
        await update.message.reply_text(f"Домашка по {subj} добавлена: {body}")
        return

# ---------------- Export ----------------
async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["== Домашка =="]
    for s, txt, due, added in db_get_hw():
        lines.append(f"{s} | {txt}")
    lines.append("\n== Контрольные ==")
    for s, date, desc in db_get_tests():
        lines.append(f"{s} | {date} | {desc}")
    lines.append("\n== Оценки ==")
    uid = update.message.from_user.id
    rows = db_get_marks(uid)
    subjects = {}
    for s, m in rows:
        subjects.setdefault(s, []).append(str(m))
    for s, m_list in subjects.items():
        avg = db_get_avg(uid, s)
        lines.append(f"{s}: {' '.join(m_list)} (ср. {avg:.2f})")
    content = "\n".join(lines)
    with open("export.txt", "w", encoding="utf-8") as f:
        f.write(content)
    await update.message.reply_document(InputFile("export.txt"))

# ---------------- Setup ----------------
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", show_today))
    app.add_handler(CommandHandler("tomorrow", show_tomorrow))
    app.add_handler(CommandHandler("hw", show_hw_cmd))
    app.add_handler(CommandHandler("add", add_menu))
    app.add_handler(CommandHandler("export", export_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dialog_text_handler))
    app.job_queue.run_daily(daily_morning_job, time=datetime.strptime("08:00", "%H:%M").time())
    app.run_polling()

if __name__ == "__main__":
    main()
