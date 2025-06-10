import os
import random
import asyncio
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from localization import gb_localization, ua_localization

# === Завантаження токена ===
load_dotenv("token.env")
TOKEN = os.getenv("BOT_TOKEN")

PHOTO_FOLDER = "photos"
user_ids = set()

# === Інтерфейси ===
language_menu = ReplyKeyboardMarkup(
    keyboard=[["🇬🇧 English", "🇺🇦 Українська"]],
    resize_keyboard=True,
    one_time_keyboard=True
)

def get_main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[lang["Projects"], lang["Help"], lang["Option"]]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_options_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[lang["Reset"]], [lang["BackToMenu"]]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# === Дані про проєкти ===
projects = {
    "shelter": {
        "title": {
            "en": "🐾 Animal Shelter Construction",
            "ua": "🐾 Будівництво Притулку"
        },
        "description": {
            "en": "We are building a new shelter for stray animals in Lviv. Donations help with materials, food, and meds.",
            "ua": "Ми будуємо новий притулок для бездомних тварин у Львові. Пожертви підуть на будматеріали, їжу та ліки."
        },
        "requisites": "IBAN: UA123456789\nCard: 1234 5678 9012 3456"
    },
    "food": {
        "title": {
            "en": "🍖 Food for Rescued Animals",
            "ua": "🍖 Їжа для урятованих тварин"
        },
        "description": {
            "en": "We provide daily meals for over 80 animals. Join our monthly support program!",
            "ua": "Щоденно годуємо понад 80 тварин. Долучайтесь до щомісячної підтримки!"
        },
        "requisites": "PayPal: food4animals@example.com\nCard: 4321 8765 2109 6543"
    },
    "clinic": {
        "title": {
            "en": "💉 Veterinary Clinic Repairs",
            "ua": "💉 Ремонт ветклініки"
        },
        "description": {
            "en": "We are repairing our small clinic for emergency surgeries. Every donation matters.",
            "ua": "Ремонтуємо нашу маленьку клініку для термінових операцій. Кожна гривня важлива!"
        },
        "requisites": "Monobank: 5375 4112 9876 1234"
    }
}

# === Команди ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        context.user_data.clear()
        user_ids.add(update.effective_chat.id)
        await update.message.reply_text(
            "Please select your language / Будь ласка, оберіть мову:",
            reply_markup=language_menu
        )

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Please select your language / Будь ласка, оберіть мову:",
        reply_markup=language_menu
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", gb_localization)
    text = "Choose an option:" if lang == gb_localization else "Оберіть опцію:"
    await update.message.reply_text(text, reply_markup=get_main_menu(lang))

async def show_options_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", gb_localization)
    await update.message.reply_text(lang["OptionMes"], reply_markup=get_options_menu(lang))

# === Повідомлення ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    chat_id = update.message.chat_id
    user_ids.add(chat_id)

    if msg == "🇬🇧 English":
        context.user_data["lang"] = gb_localization
        await update.message.reply_text(gb_localization["LocalMes"])
        await show_main_menu(update, context)
        return
    elif msg == "🇺🇦 Українська":
        context.user_data["lang"] = ua_localization
        await update.message.reply_text(ua_localization["LocalMes"])
        await show_main_menu(update, context)
        return

    lang = context.user_data.get("lang")
    if not lang:
        await update.message.reply_text("Please select a language first / Спочатку оберіть мову:")
        return

    if msg in [lang["Projects"]]:
        keyboard = [
            [InlineKeyboardButton(proj["title"]["en"] if lang == gb_localization else proj["title"]["ua"], callback_data=key)]
            for key, proj in projects.items()
        ]
        await update.message.reply_text(
            lang["ChooseProject"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif msg in [lang["Help"]]:
        await update.message.reply_text(lang["HelpMes"])

    elif msg in [lang["Option"]]:
        await show_options_menu(update, context)

    elif msg in [lang["Reset"]]:
        await restart(update, context)

    elif msg in [lang["BackToMenu"]]:
        await show_main_menu(update, context)

    else:
        await update.message.reply_text(lang["Error"])

# === Обробник вибору проєкту ===
async def handle_project_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", gb_localization)
    data = query.data
    if data in projects:
        proj = projects[data]
        title = proj["title"]["en"] if lang == gb_localization else proj["title"]["ua"]
        desc = proj["description"]["en"] if lang == gb_localization else proj["description"]["ua"]
        reqs = proj["requisites"]

        text = f"*{title}*\n\n{desc}\n\n*Requisites / Реквізити:*\n`{reqs}`"
        await query.edit_message_text(text=text, parse_mode="Markdown")

# === Адмін-меню ===
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = 123456789  # 🔒 заміни на свій Telegram ID
    if update.effective_user.id == admin_id:
        await update.message.reply_text("👑 Admin Panel:\n1. Користувачів: {}\n2. Розсилка працює...".format(len(user_ids)))
    else:
        await update.message.reply_text("🚫 You are not authorized.")

# === Розсилка ===
async def broadcast_message(application):
    while True:
        for chat_id in user_ids:
            try:
                message = "⏰ Reminder: every 90 minutes!\n⏰ Нагадування: кожні 90 хвилин!"
                await application.bot.send_message(chat_id=chat_id, text=message)

                photos = [f for f in os.listdir(PHOTO_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if photos:
                    photo_path = os.path.join(PHOTO_FOLDER, random.choice(photos))
                    with open(photo_path, 'rb') as photo:
                        await application.bot.send_photo(chat_id=chat_id, photo=photo)

            except Exception as e:
                print(f"❌ Помилка при надсиланні до {chat_id}: {e}")

        await asyncio.sleep(90 * 60)  # кожні 90 хвилин

# === Запуск бота ===
async def on_startup(app):
    asyncio.create_task(broadcast_message(app))

app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("restart", restart))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_project_selection))

app.run_polling()
