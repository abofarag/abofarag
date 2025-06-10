from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
import subprocess
print('[DEBUG] pip freeze:')
print(subprocess.getoutput('pip freeze'))

import httpx
print("[DEBUG] httpx version:", httpx.__version__)

from dotenv import load_dotenv
from .ai_agent import AIAgent
from .sheets_manager import GoogleSheetsManager
from .manychat import ManyChatAPI
from . import config

load_dotenv()

app = FastAPI(
    title="Instagram AI Support",
    description="AI-powered Instagram support bot using ManyChat",
    version="1.0.0"
)

# Initialize Google credentials (from file or env)
google_creds_path = 'config/google_credentials.json'
google_creds = None
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

@app.post("/manychat-webhook")
async def manychat_webhook(request: Request):
    """Webhook API endpoint for ManyChat integration
    IMPORTANT: تم حذف N8N تماماً من النظام
    """
    try:
        data = await request.json()
        print(f"[WEBHOOK] Received data: {data}")
        
        # Extract user data from request
        user_input = data.get("customFields", {}).get("userinput", "")
        contact_id = data.get("subscriber_id", "")
        first_name = data.get("first_name", "")
        
        print(f"[WEBHOOK] Processing message: '{user_input}' from {first_name} (ID: {contact_id})")
        
        # Default empty reply in case of error
        ai_reply = ""
        
        # 1. تعامل مع أسئلة السعر مباشرة
        price_keywords = ['سعر', 'كم', 'تكلفة', 'ريال']
        query_lower = user_input.lower()
        
        if any(keyword in query_lower for keyword in price_keywords) and ('جاسترو' in query_lower or 'زيرو' in query_lower):
            # إجابة مباشرة عن سؤال السعر
            ai_reply = "سعر منتج جاسترو زيرو هو 250 ريال."
            print(f"[WEBHOOK] Price answer generated: {ai_reply}")
        else:
            # 2. البحث في قاعدة المعرفة
            knowledge = await sheets_manager.search_knowledge_base(user_input)
            
            if knowledge and knowledge.startswith('ج:'):
                # إجابة مباشرة من قاعدة المعرفة
                ai_reply = knowledge.replace('ج: ', '')
                print(f"[WEBHOOK] Knowledge base answer: {ai_reply}")
            else:
                # 3. استخدام ChatGPT كخيار أخير
                response = await ai_agent.process_message(user_input, contact_id)
                ai_reply = response.get("output", "")
                print(f"[WEBHOOK] ChatGPT answer: {ai_reply}")
        
        # تسجيل التفاعل بشكل مباشر خارج AIAgent
        dubai_tz = pytz.timezone('Asia/Dubai')
        timestamp = datetime.now(dubai_tz).strftime('%d/%m/%Y %H:%M:%S')
        
        # محاولة تسجيل السؤال والجواب
        try:
            await sheets_manager.log_interaction(
                timestamp=timestamp,
                contact_id=contact_id,
                user_question=user_input,
                bot_answer=ai_reply
            )
            print("[WEBHOOK] Interaction logged successfully to Google Sheets")
        except Exception as e:
            print(f"[WEBHOOK] ERROR logging interaction: {str(e)}")
        
        print(f"[WEBHOOK] Returning final response to ManyChat: {ai_reply}")
        
        # عودة الرد بصيغة ManyChat
        return {
            "gpt_reply": ai_reply,
            "customFields": {
                "userinput": user_input
            }
        }
    except Exception as e:
        print(f"[ERROR] Error in manychat-webhook: {str(e)}")
        return {"error": str(e)}

@app.post("/instagram-bot")
async def manychat_webhook(request: Request):
    try:
        data = await request.json()
        # دعم كلا الصيغتين
        if "body" in data and isinstance(data["body"], dict):
            body = data["body"]
        else:
            body = data
        user_input = body.get("userInput")
        contact_id = body.get("contactId")
        if not user_input or not contact_id:
            return JSONResponse(status_code=422, content={"detail": "Missing userInput or contactId"})

        # Process message with AI agent
        response = await ai_agent.process_message(user_input, contact_id)
        
        # Send response back through ManyChat
        await manychat.send_message(
            subscriber_id=contact_id,
            message=response['output']
        )
        
        return response
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[ERROR] /instagram-bot:", tb)
        return JSONResponse(status_code=500, content={"detail": str(e), "trace": tb})

@app.get('/health')
async def health_check():
    try:
        # Test Google Sheets connection
        await sheets_manager.search_knowledge_base('test')
        return {
            'status': 'healthy',
            'components': {
                'google_sheets': 'connected',
                'openai': 'configured',
                'manychat': 'configured'
            },
            'webhook_url': f"https://instaai.herokuapp.com{config.WEBHOOK_ENDPOINT}"
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

@app.post("/manychat-webhook")
async def manychat_live_webhook(request: Request):
    try:
        data = await request.json()
        print(f"[manychat-webhook] Received request: {data}")
        # دعم كلا الصيغتين
        if "body" in data and isinstance(data["body"], dict):
            body = data["body"]
        else:
            body = data
        user_input = body.get("userInput")
        contact_id = body.get("contactId")
        print(f"[manychat-webhook] userInput: {user_input}, contactId: {contact_id}")
        if not user_input or not contact_id:
            print("[manychat-webhook] Missing userInput or contactId!")
            return JSONResponse(status_code=422, content={"detail": "Missing userInput or contactId"})

        print("[manychat-webhook] Passing message to ChatGPT...")
        response = await ai_agent.process_message(user_input, contact_id)
        print(f"[manychat-webhook] ChatGPT response: {response['output']}")
        
        # إرجاع الرد بالضبط وفقًا لصيغة JSONPath المطلوبة في ManyChat
        response_data = {
            "gpt_reply": response['output'],    # JSONPath:gpt_reply
            "custom_fields": {                  # Select Custom Field:userinput
                "userinput": user_input
            }
        }
        print(f"[manychat-webhook] Returning response to ManyChat: {response_data}")
        return response_data
    except Exception as e:
        import traceback
        print("[ERROR] /manychat-webhook:", traceback.format_exc())
        return JSONResponse(status_code=500, content={
            "detail": str(e),
            "trace": traceback.format_exc()
        })

# For Heroku deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port)
