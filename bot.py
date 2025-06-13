import os
import random
import asyncio
import json
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
Admin_Id = {5529532494}

PHOTO_FOLDER = "photos"
PROJECTS_FILE = "projects.json"
user_ids = set()

# === Завантаження/збереження проєктів ===
def load_projects():
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
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
        }
    }

def save_projects(projects_data):
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projects_data, f, ensure_ascii=False, indent=4)

projects = load_projects()

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

# === Адмін-команди ===
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in Admin_Id:
        await update.message.reply_text(
            "👑 Адмін-команди:\n"
            "/add_project - додати проєкт\n"
            "/delete_project - видалити проєкт\n"
            "/list_projects - список проєктів\n"
            f"👥 Користувачів: {len(user_ids)}\n"
            f"📂 Проєктів: {len(projects)}"
        )
    else:
        await update.message.reply_text("🚫 Ви не авторизовані.")

async def add_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Admin_Id:
        await update.message.reply_text("🚫 Ви не авторизовані.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Використання:\n"
            "/add_project <ключ>\n\n"
            "Потім бот запросить:\n"
            "1. Назву (англійською)\n"
            "2. Назву (українською)\n"
            "3. Опис (англійською)\n"
            "4. Опис (українською)\n"
            "5. Реквізити"
        )
        return
    
    project_key = context.args[0]
    if project_key in projects:
        await update.message.reply_text("❌ Цей ключ вже використовується!")
        return
    
    context.user_data["adding_project"] = True
    context.user_data["project_key"] = project_key
    context.user_data["step"] = "title_en"
    
    await update.message.reply_text("Введіть назву проєкту англійською:")

async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Admin_Id:
        await update.message.reply_text("🚫 Ви не авторизовані.")
        return
    
    if not context.args:
        project_list = "\n".join([f"/delete_project {key}" for key in projects.keys()])
        await update.message.reply_text(
            f"Доступні проєкти для видалення:\n\n{project_list}"
        )
        return
    
    project_key = context.args[0]
    if project_key in projects:
        del projects[project_key]
        save_projects(projects)
        await update.message.reply_text(f"✅ Проєкт '{project_key}' видалено!")
    else:
        await update.message.reply_text("❌ Проєкт не знайдено!")

async def list_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in Admin_Id:
        await update.message.reply_text("🚫 Ви не авторизовані.")
        return
    
    if not projects:
        await update.message.reply_text("ℹ️ Немає жодного проєкту.")
        return
    
    message = "📂 Список проєктів:\n\n"
    for key, project in projects.items():
        message += f"🔹 {key}:\n"
        message += f"EN: {project['title']['en']}\n"
        message += f"UA: {project['title']['ua']}\n\n"
    
    await update.message.reply_text(message)

# === Обробник вводу для додавання проєкту ===
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("adding_project"):
        return
    
    msg = update.message.text
    project_key = context.user_data["project_key"]
    step = context.user_data["step"]
    
    if step == "title_en":
        context.user_data["title_en"] = msg
        context.user_data["step"] = "title_ua"
        await update.message.reply_text("Введіть назву проєкту українською:")
    
    elif step == "title_ua":
        context.user_data["title_ua"] = msg
        context.user_data["step"] = "desc_en"
        await update.message.reply_text("Введіть опис проєкту англійською:")
    
    elif step == "desc_en":
        context.user_data["desc_en"] = msg
        context.user_data["step"] = "desc_ua"
        await update.message.reply_text("Введіть опис проєкту українською:")
    
    elif step == "desc_ua":
        context.user_data["desc_ua"] = msg
        context.user_data["step"] = "requisites"
        await update.message.reply_text("Введіть реквізити для донатів:")
    
    elif step == "requisites":
        projects[project_key] = {
            "title": {
                "en": context.user_data["title_en"],
                "ua": context.user_data["title_ua"]
            },
            "description": {
                "en": context.user_data["desc_en"],
                "ua": context.user_data["desc_ua"]
            },
            "requisites": msg
        }
        save_projects(projects)
        
        # Очищаємо тимчасові дані
        context.user_data.pop("adding_project")
        context.user_data.pop("project_key")
        context.user_data.pop("step")
        context.user_data.pop("title_en")
        context.user_data.pop("title_ua")
        context.user_data.pop("desc_en")
        context.user_data.pop("desc_ua")
        
        await update.message.reply_text(
            f"✅ Проєкт '{project_key}' успішно додано!",
            reply_markup=get_main_menu(context.user_data.get("lang", ua_localization))
        )

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
        await handle_admin_input(update, context)

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

# Основні команди
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("restart", restart))
app.add_handler(CommandHandler("admin", admin))

# Адмін-команди
app.add_handler(CommandHandler("add_project", add_project))
app.add_handler(CommandHandler("delete_project", delete_project))
app.add_handler(CommandHandler("list_projects", list_projects))

# Обробники повідомлень
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_project_selection))

app.run_polling()