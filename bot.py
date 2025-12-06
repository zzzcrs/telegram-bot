# bot.py
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

from db import init_db, add_user, log_action
from modules.schedule import get_day_schedule, get_week_schedule, add_schedule_entry
from modules.homework import add_hw as db_add_hw, get_hw as db_get_hw, delete_hw as db_delete_hw
from modules.tests import add_test as db_add_test, get_tests as db_get_tests
from modules.marks import add_mark as db_add_mark, get_marks as db_get_marks, get_avg as db_get_avg, clear_marks as db_clear_marks
from modules.announce import add_announce as db_add_announce, get_all_announcements
from utils.scheduler import daily_morning_job

TOKEN = '8292924282:AAFXPnq5d8cLviX4ZNQuyRgm3y-RRCLN2ZM'

# ---------------- Reply keyboard ----------------
menu_keyboard = [
    ["📅 Сегодня", "📅 Завтра"],
    ["📂 Домашка", "🧪 Контрольные"],
    ["⭐ Мои оценки", "➕ Добавить", "⚙️ Экспорт/Очистка"]
]
markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

# ---------------- Helpers ----------------
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
    await update.message.reply_text(
        "Привет! Я школьный помощник. Выбери действие или напиши команду.",
        reply_markup=markup
    )
    log_action(user.id, "start")

async def help_cmd(update: Update, context):
    await update.message.reply_text(
        "Команды:\n"
        "/today - расписание на сегодня\n"
        "/tomorrow - расписание на завтра\n"
        "/hw [предмет] - показать домашку\n"
        "/add_hw <предмет> <дата?> <текст> - добавить домашку\n"
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
        msg += f"• {subj} — {text} (срок {due_date})\n"
    await update.message.reply_text(msg)

# ---------------- User dialog state ----------------
USER_STATE = {}

# ---------------- Callback query handler ----------------
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
    elif query.data == "export":
        # вызываем экспорт
        await export_cmd(update, context)
    elif query.data == "clear_marks":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Да, удалить все", callback_data="confirm_clear")],
            [InlineKeyboardButton("Отмена", callback_data="cancel")]
        ])
        await query.edit_message_text("Уверен(а)? Это удалит ВСЕ твои оценки.", reply_markup=kb)
    elif query.data == "confirm_clear":
        db_clear_marks(user_id)
        await query.edit_message_text("Все оценки удалены.")
    elif query.data == "cancel":
        await query.edit_message_text("Отмена.")

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
        msg = "🧪 Контрольные:\n" + "\n".join([f"{s} — {d} — {desc}" for s,d,desc in tests]) if tests else "Контрольных нет."
        await update.message.reply_text(msg)
        return
    elif text == "⭐ Мои оценки":
        rows = db_get_marks(uid)
        msg = "⭐ Мои оценки:\n" + "\n".join([f"{s} — {m}" for s,m in rows]) if rows else "Оценок нет."
        await update.message.reply_text(msg)
        return
    elif text == "➕ Добавить":
        await add_menu(update, context)
        return
    elif text == "⚙️ Экспорт/Очистка":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Экспорт", callback_data="export")],
            [InlineKeyboardButton("Очистить оценки", callback_data="clear_marks")]
        ])
        await update.message.reply_text("Выберите действие:", reply_markup=kb)
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
                await update.message.reply_text("Укажи дату (YYYY-MM-DD) или 'сегодня'/'завтра' (можно пропустить):")
                return
            elif step == 2:
                maybe_date = parse_date_like(text)
                if maybe_date:
                    state["due_date"] = maybe_date
                    state["step"] = 3
                    await update.message.reply_text("Теперь напиши текст задания:")
                    return
                else:
                    state["due_date"] = datetime.now().date().isoformat()
                    state["text"] = text
                    db_add_hw(state["subject"], state["text"], state["due_date"])
                    del USER_STATE[uid]
                    await update.message.reply_text(f"Добавлено: {state['subject']} — {state['text']} (срок {state['due_date']})")
                    return
            elif step == 3:
                state["text"] = text
                db_add_hw(state["subject"], state["text"], state.get("due_date"))
                del USER_STATE[uid]
                await update.message.reply_text(f"Добавлено: {state['subject']} — {state['text']} (срок {state.get('due_date')})")
                return

        elif flow == "add_mark":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("Укажи оценку (1-5):")
                return
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
                return

        elif flow == "add_test":
            if step == 1:
                state["subject"] = text.lower()
                state["step"] = 2
                await update.message.reply_text("Укажи дату теста (YYYY-MM-DD) или 'завтра':")
                return
            elif step == 2:
                dd = parse_date_like(text)
                if not dd:
                    await update.message.reply_text("Неверная дата. Попробуй ещё раз (YYYY-MM-DD или 'завтра'):")
                    return
                state["date"] = dd
                state["step"] = 3
                await update.message.reply_text("Краткое описание теста:")
                return
            elif step == 3:
                desc = text
                db_add_test(state["subject"], state["date"], desc)
                del USER_STATE[uid]
                await update.message.reply_text(f"Контрольная по {state['subject']} запланирована на {state['date']}.")
                return

        return

    # --------- Simple NLU fallback ----------
    await simple_nlu_handler(update, context)

# ---------------- Simple NLU ----------------
async def simple_nlu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    # add mark quick
    m = re.search(r"(?:добавь|поставь)?\s*(?:оценку\s*)?(?:по\s*)?(?P<subject>\w+)\s*(?P<mark>[1-5])$", text)
    if m:
        subj = m.group("subject")
        mark = int(m.group("mark"))
        db_add_mark(update.message.from_user.id, subj, mark)
        await update.message.reply_text(f"Оценка {mark} по {subj} добавлена.")
        return

    # add hw quick
    m = re.match(r"(?:добавь|поставь)\s+домашк(?:у|а)\s+(?:по\s+)?(?P<subject>\w+)\s+(?P<text>.+)", text)
    if m:
        subj = m.group("subject")
        body = m.group("text")
        db_add_hw(subj, body, None)
        await update.message.reply_text(f"Домашка по {subj} добавлена: {body}")
        return

    # show hw
    m = re.match(r"(?:какая|покажи|что задано)\s+домашк(?:а|у)(?:\s+по\s+)?(?P<subject>\w+)", text)
    if m:
        subj = m.group("subject")
        rows = db_get_hw(subj)
        if not rows:
            await update.message.reply_text("Домашки нет.")
            return
        msg = ""
        for s, tx, due, added in rows:
            msg += f"{s} — {tx} (срок {due})\n"
        await update.message.reply_text(msg)
        return

    # show schedule
    if text in ("что сегодня", "расписание сегодня", "покажи расписание"):
        await show_today(update, context)
        return
    if text in ("что завтра", "расписание завтра"):
        await show_tomorrow(update, context)
        return

    await update.message.reply_text("Не понял. Попробуй кнопки меню или /help.")

# ---------------- Export ----------------
async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = []
    lines.append("== Домашка ==")
    for s, txt, due, added in db_get_hw():
        lines.append(f"{s} | {due} | {txt}")
    lines.append("\n== Контрольные ==")
    for s, date, desc in db_get_tests():
        lines.append(f"{s} | {date} | {desc}")
    lines.append("\n== Оценки (по тебе) ==")
    rows = db_get_marks(update.message.from_user.id)
    for s, mark in rows:
        lines.append(f"{s} | {mark}")
    content = "\n".join(lines)
    with open("export.txt", "w", encoding="utf-8") as f:
        f.write(content)
    await update.message.reply_document(InputFile("export.txt"))

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

    # callback queries
    app.add_handler(CallbackQueryHandler(on_callback))

    # messages (ReplyKeyboard + dialog + NLU)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dialog_text_handler))

    # morning job at 08:00
    app.job_queue.run_daily(daily_morning_job, time=datetime.strptime("08:00", "%H:%M").time())

    app.run_polling()

if __name__ == "__main__":
    main()
