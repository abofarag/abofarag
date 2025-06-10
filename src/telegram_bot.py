import asyncio
import logging
import os
import json
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple

import httpx
from dotenv import load_dotenv
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove,
    KeyboardButton
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackContext, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters
)
from telegram.constants import ParseMode

# تعريف أدوار المستخدمين
class UserRole(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

# تحميل قاعدة بيانات المستخدمين
try:
    with open('users_db.json', 'r') as f:
        users_db = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    users_db = {}
    # إضافة المستخدمين المدرجين في المتغيرات البيئية كمسؤولين
    admin_ids = os.getenv("ADMIN_USER_IDS", "").split(",")
    for admin_id in admin_ids:
        if admin_id.strip():
            users_db[admin_id.strip()] = {
                "name": f"Admin-{admin_id[:4]}",
                "role": UserRole.ADMIN.value,
                "joined_at": datetime.now().isoformat()
            }
    # حفظ قاعدة البيانات
    with open('users_db.json', 'w') as f:
        json.dump(users_db, f)

# --- CONFIGURATION ---
# Load environment variables from .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7656331584:AAHZi4sfK1Gm9eMX9MyHVqqB2KY7VSQIk3E")
ADMIN_USER_IDS_RAW = os.getenv("ADMIN_USER_IDS", "")
print(f"DEBUG: Loaded ADMIN_USER_IDS_RAW = '{ADMIN_USER_IDS_RAW}'") # Diagnostic print
ADMIN_USER_IDS = [uid.strip() for uid in ADMIN_USER_IDS_RAW.split(',') if uid.strip()]

# Server configuration
SERVERS = {
    "render": "https://abofarag.onrender.com",
    "heroku": "https://instaai-9630d02181e7.herokuapp.com"
}
DEFAULT_SERVER = "render"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- ADMIN CHECK DECORATOR ---
def admin_only(func):
    async def wrapped(update: Update, context: CallbackContext):
        user_id = str(update.effective_user.id)
        if user_id not in ADMIN_USER_IDS:
            await update.message.reply_text("Sorry, this is an admin-only command.")
            return
        return await func(update, context)
    return wrapped


# --- API CALLS ---
async def get_active_server(context: CallbackContext) -> str:
    """Gets the currently active server URL from bot_data."""
    return context.bot_data.get("active_server_url", SERVERS[DEFAULT_SERVER])

async def get_bot_status(context: CallbackContext) -> str:
    """Calls the FastAPI /mode endpoint to get the current status."""
    base_url = await get_active_server(context)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/mode")
            response.raise_for_status()
            mode = response.json().get("mode", "unknown")
            active_server_name = context.bot_data.get("active_server_name", DEFAULT_SERVER)
            return f"🤖 Bot status: *{mode.upper()}*\n- Active Server: *{active_server_name.upper()}*"
    except httpx.RequestError as e:
        logger.error(f"Error calling FastAPI /mode endpoint: {e}")
        return f"❌ Could not connect to the main bot at {base_url}. Is it running?"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred."

async def set_bot_mode(context: CallbackContext, mode: str) -> str:
    """Calls the FastAPI /mode endpoint to set the bot's mode."""
    base_url = await get_active_server(context)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}/mode", json={"mode": mode})
            response.raise_for_status()
            new_mode = response.json().get("mode", "unknown")
            return f"✅ Bot mode successfully set to *{new_mode.upper()}*"
    except httpx.RequestError as e:
        logger.error(f"Error setting bot mode: {e}")
        return f"❌ Could not change the bot mode. Is the main bot running at {base_url}?"
    except Exception as e:
        logger.error(f"An unexpected error occurred while setting mode: {e}")
        return "An unexpected error occurred."

# --- COMMAND HANDLERS ---
async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message and keyboard"""
    try:
        user = update.effective_user
        user_id = str(user.id)
        user_name = user.first_name or "User"
        
        # Create keyboard with main commands
        keyboard = [
            [KeyboardButton("/status"), KeyboardButton("/switch_server")],
            [KeyboardButton("/learn"), KeyboardButton("/reply")],
            [KeyboardButton("/manychat"), KeyboardButton("/users")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Add user to database if not exists
        if user_id not in users_db:
            users_db[user_id] = {
                "name": user_name,
                "role": "viewer",  # Default role
                "joined_at": datetime.now().isoformat()
            }
            save_users_db()
        
        # Send welcome message
        welcome_text = (
            f"👋 مرحباً {user_name}!\n"
            "🤖 أنا بوت تحكم دعم AI Support Bot\n\n"
            "🔹 /status - عرض حالة البوت\n"
            "🔄 /switch_server - تبديل السيرفر\n"
            "📚 /learn - وضع التعلم\n"
            "💬 /reply - وضع الردود\n"
            "⚙️ /manychat - إعدادات ManyChat\n"
            "👥 /users - إدارة المستخدمين"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"User {user_id} ({user_name}) started the bot")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(
            "⚠️ عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقاً."
        )

@admin_only
async def status_command(update: Update, context: CallbackContext) -> None:
    """Gets and sends the current bot status."""
    message = await get_bot_status(context)
    await update.message.reply_text(message, parse_mode='Markdown')

@admin_only
async def learn_command(update: Update, context: CallbackContext) -> None:
    """Sets the bot to learning mode."""
    message = await set_bot_mode(context, 'learning')
    await update.message.reply_text(message, parse_mode='Markdown')

@admin_only
async def reply_command(update: Update, context: CallbackContext) -> None:
    """Sets the bot to reply mode (command mode)."""
    message = await set_bot_mode(context, 'reply')
    await update.message.reply_text(message, parse_mode='Markdown')

@admin_only
async def switch_server_command(update: Update, context: CallbackContext) -> None:
    """Displays a keyboard to switch servers."""
    keyboard = [
        [InlineKeyboardButton(name.upper(), callback_data=f"server_{name}")] for name in SERVERS.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a server to activate:", reply_markup=reply_markup)

async def switch_server_callback(update: Update, context: CallbackContext) -> None:
    """Handles the server switch callback."""
    query = update.callback_query
    await query.answer()
    server_name = query.data.split("_")[1]
    
    if server_name in SERVERS:
        context.bot_data["active_server_name"] = server_name
        context.bot_data["active_server_url"] = SERVERS[server_name]
        await query.edit_message_text(text=f"✅ Active server switched to *{server_name.upper()}*.", parse_mode='Markdown')
    else:
        await query.edit_message_text(text="❌ Invalid server selected.")

# --- MAIN FUNCTION ---
def is_admin(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم مشرفًا"""
    return str(user_id) in users_db and users_db[str(user_id)]["role"] == UserRole.ADMIN.value

def is_editor(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم محررًا أو مشرفًا"""
    user_id = str(user_id)
    return user_id in users_db and users_db[user_id]["role"] in [UserRole.ADMIN.value, UserRole.EDITOR.value]

def save_users_db():
    """حفظ قاعدة بيانات المستخدمين إلى ملف"""
    with open('users_db.json', 'w') as f:
        json.dump(users_db, f)

async def admin_required(update: Update, context: CallbackContext) -> bool:
    """ديكوراتور للتحقق من صلاحيات المشرف"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ عذرًا، هذا الأمر متاح فقط للمشرفين.")
        return False
    return True

async def editor_required(update: Update, context: CallbackContext) -> bool:
    """ديكوراتور للتحقق من صلاحيات المحرر أو المشرف"""
    if not is_editor(update.effective_user.id):
        await update.message.reply_text("⛔️ عذرًا، هذا الأمر يتطلب صلاحيات محرر أو أعلى.")
        return False
    return True

# --- أوامر ManyChat ---
@admin_required
async def manychat_control(update: Update, context: CallbackContext) -> None:
    """لوحة تحكم ManyChat الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("📋 قائمة الصفحات", callback_data='mc_list_pages')],
        [InlineKeyboardButton("➕ إضافة صفحة", callback_data='mc_add_page')],
        [InlineKeyboardButton("⚙️ إعدادات الصفحة", callback_data='mc_page_settings')],
        [InlineKeyboardButton("📊 إحصائيات", callback_data='mc_stats')],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🛠️ <b>لوحة تحكم ManyChat</b>\n\n"
        "اختر الإجراء المطلوب:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

# --- أوامر إدارة المستخدمين ---
@admin_required
async def manage_users(update: Update, context: CallbackContext) -> None:
    """إدارة المستخدمين"""
    keyboard = [
        [InlineKeyboardButton("👥 عرض المستخدمين", callback_data='list_users')],
        [InlineKeyboardButton("➕ إضافة مستخدم", callback_data='add_user')],
        [InlineKeyboardButton("✏️ تعديل صلاحيات", callback_data='edit_user')],
        [InlineKeyboardButton("🗑️ حذف مستخدم", callback_data='delete_user')],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👥 <b>إدارة المستخدمين</b>\n\n"
        "اختر الإجراء المطلوب:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def list_users(update: Update, context: CallbackContext) -> None:
    """عرض قائمة المستخدمين"""
    if not await admin_required(update, context):
        return
        
    if not users_db:
        await update.callback_query.message.reply_text("❌ لا يوجد مستخدمين مسجلين بعد.")
        return
        
    users_list = "👥 *قائمة المستخدمين:*\n\n"
    for user_id, user_data in users_db.items():
        users_list += f"🆔 `{user_id}` - {user_data.get('name', 'بدون اسم')} - {user_data['role']}\n"
    
    await update.callback_query.message.reply_text(users_list, parse_mode=ParseMode.MARKDOWN)

# --- معالجة الأزرار ---
async def button_handler(update: Update, context: CallbackContext) -> None:
    """معالجة الأزرار"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'mc_list_pages':
        await list_manychat_pages(update, context)
    elif query.data == 'users_list':
        await list_users(update, context)
    elif query.data == 'main_menu':
        await start(update, context)
    # يمكنك إضافة المزيد من معالجات الأزرار هنا

def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    if update and isinstance(update, Update) and update.effective_message:
        update.effective_message.reply_text('عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقاً.')

def log_all_messages(update: Update, context: CallbackContext) -> None:
    """Log all messages"""
    logger.info(f"Message from {update.effective_user.id}: {update.message.text}")

def main() -> None:
    """Run the bot."""
    print("Starting Telegram bot controller (sync main)...")
    
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Set default server
    application.bot_data["active_server_name"] = DEFAULT_SERVER
    application.bot_data["active_server_url"] = SERVERS[DEFAULT_SERVER]
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("reply", reply_command))
    application.add_handler(CommandHandler("switch_server", switch_server_command))
    application.add_handler(CommandHandler("manychat", manychat_control))
    application.add_handler(CommandHandler("users", manage_users))
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(switch_server_callback, pattern="^server_"))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Log all messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_all_messages))
    
    # Log all errors
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("Starting polling...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
