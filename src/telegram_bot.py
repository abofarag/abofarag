import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

# Construct the path to the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

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
    """Sends a message when the command /start is issued."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}!\nWelcome to the AI Support Bot controller.\n\nUse the commands below to manage the bot's behavior.",
        reply_markup=reply_markup
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gets and sends the current bot status."""
    message = await get_bot_status()
    await update.message.reply_text(message, parse_mode='Markdown')

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the bot to learning mode."""
    message = await set_bot_mode('learning')
    await update.message.reply_text(message, parse_mode='Markdown')

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the bot to reply mode."""
    message = await set_bot_mode('reply')
    await update.message.reply_text(message, parse_mode='Markdown')


# --- MAIN FUNCTION ---
def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("reply", reply_command))

    # Start the Bot
    logger.info("Starting Telegram bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
