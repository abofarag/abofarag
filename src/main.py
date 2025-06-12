import os
import json
import logging
import asyncio
import subprocess
import httpx
import pytz 

from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# --- LOGGING SETUP (THE FIX IS HERE) ---
# This section was missing, which caused the 'NameError: name 'logger' is not defined' crash.
# It configures the logging system for the application.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- DOTENV & LOCAL IMPORTS ---
# Construct the path to the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Import local modules from the project structure
from src.ai_agent import AIAgent
from src.sheets_manager import GoogleSheetsManager
from src.manychat import ManyChatAPI
from src import config
# Import the main function from telegram_bot.py, renaming it to avoid clashes
from src.telegram_bot import main as run_telegram_bot_async

# Initial debug prints
logger.info('[DEBUG] pip freeze:\n' + subprocess.getoutput('pip freeze'))
logger.info(f"[DEBUG] httpx version: {httpx.__version__}")


# --- LIFESPAN MANAGEMENT ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("Lifespan event: Application startup...")
    logger.info("Lifespan: Attempting to start Telegram bot as a background task...")
    
    # Create a background task for the Telegram bot
    bot_task = asyncio.create_task(run_telegram_bot_async())
    
    try:
        yield # The application runs here
    finally:
        # Shutdown logic
        logger.info("Lifespan: Shutting down Telegram bot task...")
        if not bot_task.done():
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                logger.info("Lifespan: Telegram bot task successfully cancelled.")
            except Exception as e:
                logger.error(f"Lifespan: Error during bot task shutdown: {e}")

# --- FASTAPI APP INITIALIZATION ---
app = FastAPI(
    lifespan=lifespan,
    title="Instagram AI Support",
    description="AI-powered Instagram support bot using ManyChat",
    version="1.0.0"
)

# --- STATE MANAGEMENT ---
class BotState(BaseModel):
    mode: str  # Should be 'reply' or 'learning'

# Simple in-memory state. Resets on server restart.
bot_state = BotState(mode='reply')


# --- INITIALIZATION OF SERVICES ---
logger.info("Initializing services (Google Sheets, AI Agent, ManyChat)...")
google_creds = None
google_creds_path = 'config/google_credentials.json'
if os.path.exists(google_creds_path):
    with open(google_creds_path) as f:
        google_creds = json.load(f)
else:
    google_creds_env = os.getenv('GOOGLE_CREDENTIALS')
    if google_creds_env:
        google_creds = json.loads(google_creds_env)
    else:
        logger.error("FATAL: Google credentials not found in file or environment variable!")
        raise Exception("Google credentials not found!")

sheets_manager = GoogleSheetsManager(
    spreadsheet_id=config.SPREADSHEET_ID,
    credentials_dict=google_creds
)
ai_agent = AIAgent(
    openai_api_key=os.getenv('OPENAI_API_KEY', ''),
    sheets_manager=sheets_manager
)
manychat = ManyChatAPI(api_key=config.MANYCHAT_API_KEY)
logger.info("Services initialized successfully.")


# --- WEBHOOK ENDPOINT ---
@app.post("/manychat-webhook")
async def manychat_webhook(request: Request):
    """Main webhook to handle all incoming ManyChat requests."""
    try:
        data = await request.json()
        logger.info(f"[WEBHOOK] Received data: {json.dumps(data, indent=2)}")

        # --- LEARNING MODE ---
        if bot_state.mode == 'learning':
            logger.info("[WEBHOOK] Bot is in LEARNING mode.")
            question = data.get("customer_question")
            answer = data.get("moderator_answer")

            if question and answer:
                logger.info(f"[LEARN] Captured from webhook: Q: '{question}' | A: '{answer}'")
                success = await sheets_manager.add_knowledge(question, answer)
                if success:
                    logger.info("[LEARN] Knowledge added successfully from webhook.")
                    return JSONResponse(content={"status": "learned"})
                else:
                    logger.error("[LEARN] ERROR: Failed to add knowledge from webhook.")
                    return JSONResponse(content={"status": "learning_failed_sheets"})
            else:
                logger.warning("[LEARN] Ignoring learning request due to missing payload.")
                return JSONResponse(content={"status": "ignored_learning_payload"})

        # --- REPLY MODE ---
        logger.info("[WEBHOOK] Bot is in REPLY mode.")
        user_input = data.get("userInput") or data.get("customFields", {}).get("userinput", "")
        contact_id = str(data.get("contactId") or data.get("subscriber_id", ""))
        first_name = data.get("first_name", "")

        if not user_input:
            logger.warning("[WEBHOOK] No user input found. Ignoring request.")
            return JSONResponse(content={"status": "ignored", "reason": "no user input"})

        logger.info(f"[WEBHOOK] Processing message: '{user_input}' from {first_name} (ID: {contact_id})")

        ai_reply = ""
        query_lower = user_input.lower()
        price_keywords = ['سعر', 'كم', 'تكلفة', 'ريال']
        if any(keyword in query_lower for keyword in price_keywords) and ('جاسترو' in query_lower or 'زيرو' in query_lower):
            ai_reply = "سعر منتج جاسترو زيرو هو 250 ريال."
            logger.info(f"[WEBHOOK] Price answer generated: {ai_reply}")
        else:
            knowledge = await sheets_manager.search_knowledge_base(user_input)
            if knowledge and knowledge.startswith('ج:'):
                ai_reply = knowledge.replace('ج: ', '', 1)
                logger.info(f"[WEBHOOK] Knowledge base answer: {ai_reply}")
            else:
                response = await ai_agent.process_message(user_input, contact_id)
                ai_reply = response.get("output", "")
                logger.info(f"[WEBHOOK] ChatGPT answer: {ai_reply}")

        dubai_tz = pytz.timezone('Asia/Dubai')
        timestamp = datetime.now(dubai_tz).strftime('%d/%m/%Y %H:%M:%S')
        await sheets_manager.log_interaction(
            timestamp=timestamp, contact_id=contact_id, user_question=user_input, bot_answer=ai_reply
        )
        logger.info("[WEBHOOK] Interaction logged successfully.")

        response_payload = {"output": ai_reply, "customFields": {"userinput": user_input}}
        logger.info(f"[WEBHOOK] Full JSON payload to ManyChat: {response_payload}")
        return JSONResponse(content=response_payload)

    except Exception as e:
        import traceback
        logger.error(f"[ERROR] Unhandled exception in webhook: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred."})

# --- HEALTH & MODE ENDPOINTS ---
@app.get("/mode", response_model=BotState)
async def get_mode():
    """Gets the current operating mode of the bot."""
    return bot_state

@app.post("/mode", response_model=BotState)
async def set_mode(new_state: BotState):
    """Sets the operating mode of the bot ('reply' or 'learning')."""
    if new_state.mode not in ['reply', 'learning']:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'reply' or 'learning'.")
    global bot_state
    bot_state.mode = new_state.mode
    logger.info(f"[MODE] Bot mode changed to: {bot_state.mode}")
    return bot_state

# --- Uvicorn Runner for local development ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Uvicorn server on host 0.0.0.0, port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
