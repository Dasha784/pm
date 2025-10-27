import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# 🔑 Токен и настройки
TOKEN = "8325150191:AAGJ2Cg7WxQ3ltNnRj3VMBcZGrtmq9A1djo"
ADMIN_ID = 914123397
CHANNEL_ID = -1002858204554

# 🎯 Этапы диалога
CHOOSE_CATEGORY, TYPING_MESSAGE = range(2)

# 📌 Настройка логов
logging.basicConfig(level=logging.INFO)


# 🧩 Стартовая функция
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! В этом боте ты можешь оставить:\n\n"
        "💡 предложение\n📢 заявку на рекламу\n⭐️ отзыв\n\n"
        "Если что-то заинтересует администратора, он обязательно свяжется с тобой.\n\n"
        "Выбери, что ты хочешь оставить:"
    )

    keyboard = [
        [
            InlineKeyboardButton("📢 Реклама", callback_data="category_ad"),
            InlineKeyboardButton("💡 Предложение", callback_data="category_suggestion"),
        ],
        [InlineKeyboardButton("⭐️ Отзыв", callback_data="category_feedback")],
    ]

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSE_CATEGORY


# 🎯 Обработка выбора категории
async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_menu":
        return await start(update, context)

    context.user_data["category"] = query.data
    readable = {
        "category_ad": "рекламу",
        "category_suggestion": "предложение",
        "category_feedback": "отзыв",
    }

    text = (
        f"✍️ Пожалуйста, напиши своё сообщение по категории: *{readable[query.data]}*.\n"
        "Оно будет переслано администратору."
    )

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    return TYPING_MESSAGE


# 💬 Обработка сообщения пользователя
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category_map = {
        "category_ad": "📢 Реклама",
        "category_suggestion": "💡 Предложение",
        "category_feedback": "⭐️ Отзыв",
    }

    category = context.user_data.get("category", "Без категории")
    category_label = category_map.get(category, category)
    username = update.effective_user.username or f"id {update.effective_user.id}"

    message_text = (
        f"📨 Новое сообщение от @{username}\n"
        f"📂 Категория: {category_label}\n\n"
        f"{update.message.text}"
    )

    await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text)

    await update.message.reply_text("✅ Спасибо! Ваше сообщение отправлено администратору.")

    return ConversationHandler.END


# 🔚 Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("❌ Действие отменено.")
    elif update.callback_query:
        await update.callback_query.message.edit_text("❌ Действие отменено.")
    return ConversationHandler.END


# 📩 Команда 1: отправка по user_id
async def send_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Использование: /sendto <user_id> <текст>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ user_id должен быть числом")
        return

    message_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await update.message.reply_text(f"✅ Сообщение отправлено пользователю {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке: {e}")


# 📩 Команда 2: отправка по @username
async def send_to_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Использование: /sendtouser <username> <текст>")
        return

    username = context.args[0]
    if username.startswith("@"):
        username = username[1:]

    message_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=f"@{username}", text=message_text)
        await update.message.reply_text(f"✅ Сообщение отправлено пользователю @{username}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке: {e}")


# 🚀 Главная функция
def main():
    app = Application.builder().token(TOKEN).build()

    # диалог
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_CATEGORY: [CallbackQueryHandler(choose_category)],
            TYPING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                CallbackQueryHandler(choose_category),  # кнопка "назад"
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    # команды админа
    app.add_handler(CommandHandler("sendto", send_to_user))  # по id
    app.add_handler(CommandHandler("sendtouser", send_to_username))  # по username

    print("🚀 Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
