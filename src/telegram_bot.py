import os
import logging
import httpx
from functools import wraps
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

# --- ENVIRONMENT VARIABLES & CONFIGURATION ---
# Construct the path to the .env file in the project root (assuming src folder)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Use a specific logger for this module
logger = logging.getLogger(__name__)

# Load configuration from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

# --- ADMIN CONFIGURATION (MODIFIED) ---
# NOTE: It's highly recommended to use environment variables for security.
# This code first tries to load admin IDs from the 'ADMIN_USER_IDS' environment variable.
# If it's not found, it falls back to a hardcoded ID for easy setup.

ADMIN_USER_IDS_RAW = os.getenv("ADMIN_USER_IDS")
ADMIN_IDS = set()

if ADMIN_USER_IDS_RAW:
    # Use IDs from the environment variable if it is set
    logger.info("Found ADMIN_USER_IDS environment variable. Using it for configuration.")
    try:
        ADMIN_IDS = {int(user_id.strip()) for user_id in ADMIN_USER_IDS_RAW.split(',')}
        logger.info(f"Successfully loaded {len(ADMIN_IDS)} admin(s) from environment variable.")
    except ValueError:
        logger.error("FATAL: ADMIN_USER_IDS environment variable contains non-integer values. Please check it.")
        exit()
else:
    # --- الرقم الخاص بك ---
    # هذا هو الرقم الذي سيتم استخدامه كمسؤول إذا لم يتم العثور على متغير البيئة
    HARDCODED_ADMIN_ID = 1370845765
    # --- --- ---

    # Fallback to the hardcoded ID if the environment variable is not set
    logger.warning(f"WARNING: ADMIN_USER_IDS environment variable not set. Falling back to the hardcoded admin ID: {HARDCODED_ADMIN_ID}")
    ADMIN_IDS = {HARDCODED_ADMIN_ID}


# --- ADMIN DECORATOR ---
def admin_required(func):
    """
    Decorator that restricts the use of a command to admin users only.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Check if the user's ID is in the list of admin IDs
        if update.effective_user.id not in ADMIN_IDS:
            logger.warning(f"Unauthorized access attempt by user_id: {update.effective_user.id}")
            await update.message.reply_text("❌ أنت غير مصرح لك باستخدام هذا الأمر.")
            return # Stop further execution
        # If authorized, execute the original command function
        return await func(update, context, *args, **kwargs)
    return wrapper


# --- KEYBOARD ---
keyboard = [
    [KeyboardButton("/status")],
    [KeyboardButton("/learn"), KeyboardButton("/reply")]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# --- API CALLS ---
async def get_bot_status() -> str:
    """Calls the FastAPI /mode endpoint to get the current status."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/mode")
            response.raise_for_status()
            mode = response.json().get("mode", "unknown")
            return f"🤖 Bot status: *{mode.upper()}*"
    except httpx.RequestError as e:
        logger.error(f"Error calling FastAPI /mode endpoint: {e}")
        return "❌ Could not connect to the main bot. Is it running?"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred."

async def set_bot_mode(mode: str) -> str:
    """Calls the FastAPI /mode endpoint to set the bot's mode."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_BASE_URL}/mode", json={"mode": mode})
            response.raise_for_status()
            new_mode = response.json().get("mode", "unknown")
            return f"✅ Bot mode successfully set to *{new_mode.upper()}*"
    except httpx.RequestError as e:
        logger.error(f"Error setting bot mode: {e}")
        return "❌ Could not change the bot mode. Is the main bot running?"
    except Exception as e:
        logger.error(f"An unexpected error occurred while setting mode: {e}")
        return "An unexpected error occurred."


# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the command /start is issued."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}!\nWelcome to the AI Support Bot controller.\n\nUse the commands below to manage the bot's behavior.",
        reply_markup=reply_markup
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the current bot status. Available to everyone."""
    message = await get_bot_status()
    await update.message.reply_text(message, parse_mode='Markdown')

@admin_required
async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the bot to learning mode. Restricted to admins."""
    message = await set_bot_mode('learning')
    await update.message.reply_text(message, parse_mode='Markdown')

@admin_required
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the bot to reply mode. Restricted to admins."""
    message = await set_bot_mode('reply')
    await update.message.reply_text(message, parse_mode='Markdown')


# --- MAIN FUNCTION ---
def main() -> None:
    """Start the bot and set up handlers."""
    if not TELEGRAM_TOKEN:
        logger.error("FATAL: TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("reply", reply_command))

    # Start the Bot
    logger.info("Starting Telegram bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
