from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

USER_STATE = {}

def add_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Домашка", callback_data="add_hw")],
        [InlineKeyboardButton("Оценка", callback_data="add_mark")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Что добавить?", reply_markup=add_menu_keyboard())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "add_hw":
        USER_STATE[uid] = {"flow": "add_hw", "step": 1}
        await query.edit_message_text("Введите предмет для домашки:")
    elif query.data == "add_mark":
        USER_STATE[uid] = {"flow": "add_mark", "step": 1}
        await query.edit_message_text("Введите предмет для оценки:")

async def dialog_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    if uid in USER_STATE:
        state = USER_STATE[uid]
        flow = state["flow"]
        step = state["step"]

        if flow == "add_hw" and step == 1:
            state["subject"] = text
            state["step"] = 2
            await update.message.reply_text("Введите текст задания:")
            return
        if flow == "add_hw" and step == 2:
            state["text"] = text
            await update.message.reply_text(f"Добавлена домашка: {state['subject']} — {state['text']}")
            del USER_STATE[uid]
            return

        if flow == "add_mark" and step == 1:
            state["subject"] = text
            state["step"] = 2
            await update.message.reply_text("Введите оценку (1-5):")
            return
        if flow == "add_mark" and step == 2:
            state["mark"] = text
            await update.message.reply_text(f"Добавлена оценка: {state['subject']} — {state['mark']}")
            del USER_STATE[uid]
            return

    else:
        await update.message.reply_text("Не понял, попробуй /start")

app = ApplicationBuilder().token("8292924282:AAFXPnq5d8cLviX4ZNQuyRgm3y-RRCLN2ZM").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(on_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dialog_text))
app.run_polling()
