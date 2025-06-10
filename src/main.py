from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
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

# Initialize components
with open('config/google_credentials.json') as f:
    google_creds = json.load(f)

sheets_manager = GoogleSheetsManager(
    spreadsheet_id=config.SPREADSHEET_ID,
    credentials_dict=google_creds
)

ai_agent = AIAgent(
    openai_api_key=os.getenv('OPENAI_API_KEY', ''),
    sheets_manager=sheets_manager
)

manychat = ManyChatAPI(api_key=config.MANYCHAT_API_KEY)

class WebhookRequest(BaseModel):
    body: Dict[str, Any]

@app.post(config.WEBHOOK_ENDPOINT)
async def handle_webhook(request: WebhookRequest):
    try:
        # Extract data from webhook
        user_input = request.body.get('userInput')
        contact_id = request.body.get('contactId')
        
        if not user_input or not contact_id:
            raise HTTPException(
                status_code=400, 
                detail='Missing required fields: userInput or contactId'
            )
        
        # Process message with AI agent
        response = await ai_agent.process_message(user_input, contact_id)
        
        # Send response back through ManyChat
        await manychat.send_message(
            subscriber_id=contact_id,
            message=response['output']
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# For Heroku deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port)
