import asyncio
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
import logging
import os
import asyncio
import json
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import pytz
import httpx
from dotenv import load_dotenv
from enum import Enum
import csv
from io import StringIO

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
    """Sends a welcome message and keyboard."""
    user_name = update.effective_user.first_name
    keyboard = [
        [KeyboardButton("/status")],
        [KeyboardButton("/learn"), KeyboardButton("/reply")],
        [KeyboardButton("/switch_server")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"Hi {user_name}!\nWelcome to the AI Support Bot controller.",
        reply_markup=reply_markup
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
async def manychat_control(update: Update, context: CallbackContext) -> None:
    """لوحة تحكم ManyChat الرئيسية"""
    if not await admin_required(update, context):
        return
        
    keyboard = [
        [InlineKeyboardButton("📋 قائمة الصفحات", callback_data='mc_list_pages')],
        [InlineKeyboardButton("➕ إضافة صفحة", callback_data='mc_add_page')],
        [InlineKeyboardButton("⚙️ إعدادات الصفحة", callback_data='mc_page_settings')],
        [InlineKeyboardButton("📊 إحصائيات", callback_data='mc_stats')],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 *لوحة تحكم ManyChat*\n\nاختر الإجراء المطلوب:", 
                                  reply_markup=reply_markup,
                                  parse_mode=ParseMode.MARKDOWN)

# --- أوامر إدارة المستخدمين ---
async def manage_users(update: Update, context: CallbackContext) -> None:
    """إدارة المستخدمين"""
    if not await admin_required(update, context):
        return
        
    keyboard = [
        [InlineKeyboardButton("👥 عرض المستخدمين", callback_data='users_list')],
        [InlineKeyboardButton("➕ إضافة مستخدم", callback_data='users_add')],
        [InlineKeyboardButton("✏️ تعديل صلاحيات", callback_data='users_edit')],
        [InlineKeyboardButton("🗑 حذف مستخدم", callback_data='users_delete')],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👥 *إدارة المستخدمين*\n\nاختر الإجراء المطلوب:", 
                                  reply_markup=reply_markup,
                                  parse_mode=ParseMode.MARKDOWN)

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

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    if not ADMIN_USER_IDS:
        logger.error("ADMIN_USER_IDS environment variable not set! Bot will not respond to admin commands.")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.bot_data["active_server_name"] = DEFAULT_SERVER
    application.bot_data["active_server_url"] = SERVERS[DEFAULT_SERVER]

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("reply", reply_command))
    application.add_handler(CommandHandler("switch_server", switch_server_command))
    application.add_handler(CommandHandler("manychat", manychat_control))
    application.add_handler(CommandHandler("users", manage_users))
    
    # إضافة معالجات الأزرار
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CallbackQueryHandler(switch_server_callback, pattern="^server_"))

    async def log_all_messages(update: Update, context: CallbackContext):
        logger.info(f"Received message: {update.message.text} from user: {update.effective_user.id}")
    application.add_handler(MessageHandler(filters.ALL, log_all_messages))

    logger.info("Starting Telegram bot controller (sync main)...")
    application.run_polling()

if __name__ == "__main__":
    main()
