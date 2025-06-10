from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import pytz
import os
import json
import subprocess
import httpx
from dotenv import load_dotenv

# Construct the path to the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Local imports
from .ai_agent import AIAgent
from .sheets_manager import GoogleSheetsManager
from .manychat import ManyChatAPI
from . import config

# Initial debug prints
print('[DEBUG] pip freeze:')
print(subprocess.getoutput('pip freeze'))
print("[DEBUG] httpx version:", httpx.__version__)

load_dotenv()

app = FastAPI(
    title="Instagram AI Support",
    description="AI-powered Instagram support bot using ManyChat",
    version="1.0.0"
)

# --- STATE MANAGEMENT ---
class BotState(BaseModel):
    mode: str  # Should be 'reply' or 'learning'

# A simple in-memory state.
# NOTE: This will reset if the server restarts. For production, consider a persistent store.
bot_state = BotState(mode='reply')


# --- INITIALIZATION ---
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
        raise Exception("Google credentials not found in file or environment variable!")

sheets_manager = GoogleSheetsManager(
    spreadsheet_id=config.SPREADSHEET_ID,
    credentials_dict=google_creds
)

ai_agent = AIAgent(
    openai_api_key=os.getenv('OPENAI_API_KEY', ''),
    sheets_manager=sheets_manager
)

manychat = ManyChatAPI(api_key=config.MANYCHAT_API_KEY)


# --- WEBHOOK ENDPOINT ---
@app.post("/manychat-webhook")
async def manychat_webhook(request: Request):
    """
    Main webhook to handle all incoming ManyChat requests.
    It operates in two modes: 'reply' and 'learning'.
    """
    try:
        data = await request.json()
        print(f"[WEBHOOK] Received data: {json.dumps(data, indent=2)}")

        # --- LEARNING MODE --- 
        if bot_state.mode == 'learning':
            print("[WEBHOOK] Bot is in LEARNING mode.")
            question = data.get("customer_question")
            answer = data.get("moderator_answer")

            if question and answer:
                print(f"[LEARN] Captured from webhook: Q: '{question}' | A: '{answer}'")
                try:
                    success = await sheets_manager.add_knowledge(question, answer)
                    if success:
                        print("[LEARN] Knowledge added successfully from webhook.")
                        return JSONResponse(content={"status": "learned"}, status_code=200)
                    else:
                        print("[LEARN] ERROR: Failed to add knowledge from webhook.")
                        return JSONResponse(content={"status": "learning_failed_sheets"}, status_code=200)
                except Exception as e:
                    print(f"[LEARN] ERROR: Exception during learning from webhook: {str(e)}")
                    return JSONResponse(content={"status": "learning_error_internal"}, status_code=500)
            else:
                print(f"[LEARN] Ignoring learning mode request due to missing 'customer_question' or 'moderator_answer'.")
                return JSONResponse(content={"status": "ignored_learning_payload"}, status_code=200)

        # --- REPLY MODE --- 
        print("[WEBHOOK] Bot is in REPLY mode.")
        user_input = data.get("userInput")
        contact_id = data.get("contactId")
        first_name = data.get("first_name", "")

        if user_input is None:
            user_input = data.get("customFields", {}).get("userinput", "")
        if contact_id is None:
            contact_id = data.get("subscriber_id", "")

        contact_id = str(contact_id) if contact_id is not None else ""
        user_input = str(user_input) if user_input is not None else ""

        if not user_input:
            print("[WEBHOOK] No user input found. Ignoring request.")
            return JSONResponse(content={"status": "ignored", "reason": "no user input"})

        print(f"[WEBHOOK] Processing message: '{user_input}' from {first_name} (ID: {contact_id})")

        ai_reply = ""
        query_lower = user_input.lower()
        price_keywords = ['سعر', 'كم', 'تكلفة', 'ريال']
        if any(keyword in query_lower for keyword in price_keywords) and ('جاسترو' in query_lower or 'زيرو' in query_lower):
            ai_reply = "سعر منتج جاسترو زيرو هو 250 ريال."
            print(f"[WEBHOOK] Price answer generated: {ai_reply}")
        else:
            knowledge = await sheets_manager.search_knowledge_base(user_input)
            if knowledge and knowledge.startswith('ج:'):
                ai_reply = knowledge.replace('ج: ', '', 1)
                print(f"[WEBHOOK] Knowledge base answer: {ai_reply}")
            else:
                response = await ai_agent.process_message(user_input, contact_id)
                ai_reply = response.get("output", "")
                print(f"[WEBHOOK] ChatGPT answer: {ai_reply}")

        dubai_tz = pytz.timezone('Asia/Dubai')
        timestamp = datetime.now(dubai_tz).strftime('%d/%m/%Y %H:%M:%S')
        try:
            await sheets_manager.log_interaction(
                timestamp=timestamp, contact_id=contact_id, user_question=user_input, bot_answer=ai_reply
            )
            print("[WEBHOOK] Interaction logged successfully.")
        except Exception as e:
            print(f"[WEBHOOK] ERROR logging interaction: {str(e)}")

        response_payload = {"output": ai_reply, "customFields": {"userinput": user_input}}
        print(f"[WEBHOOK] Full JSON payload to ManyChat: {response_payload}")
        return JSONResponse(content=response_payload)

    except Exception as e:
        import traceback
        print(f"[ERROR] Unhandled exception in manychat-webhook: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred."})


# --- LEARNING ENDPOINT ---
class LearnRequest(BaseModel):
    question: str
    answer: str

@app.post("/learn")
async def learn_endpoint(request: LearnRequest):
    """Endpoint to manually add a new question and answer to the knowledge base."""
    try:
        print(f"[LEARN] Received new knowledge: Q: {request.question} | A: {request.answer}")
        success = await sheets_manager.add_knowledge(request.question, request.answer)
        if success:
            return JSONResponse(content={"status": "success", "message": "Knowledge added successfully."})
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge to Google Sheets.")
    except Exception as e:
        print(f"[LEARN] Error processing learn request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


# --- HEALTH & MODE ENDPOINTS ---
@app.get('/health')
async def health_check():
    """Health check endpoint to verify connections."""
    try:
        await sheets_manager.search_knowledge_base('health_check')
        openai_status = 'configured' if os.getenv('OPENAI_API_KEY') else 'not_configured'
        return JSONResponse(content={
            'status': 'healthy',
            'components': {'google_sheets': 'connected', 'openai': openai_status, 'manychat': 'configured'}
        })
    except Exception as e:
        print(f"[HEALTH CHECK] Error: {str(e)}")
        return JSONResponse(status_code=503, content={
            'status': 'unhealthy', 'error': 'Failed to connect to one or more services.', 'details': str(e)
        })

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
    print(f"[MODE] Bot mode changed to: {bot_state.mode}")
    return bot_state


# --- Uvicorn Runner for Heroku ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
