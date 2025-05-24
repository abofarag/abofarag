from fastapi import FastAPI, HTTPException, Request
from ..services.ai_service import AIService
from ..core.database import Database
from ..models.customer import Message
from datetime import datetime
import json

app = FastAPI()
ai_service = AIService()

@app.post("/webhook/manychat")
async def manychat_webhook(request: Request):
    """
    Endpoint to receive messages from ManyChat
    """
    try:
        data = await request.json()
        
        # Extract customer info and message
        customer_id = data.get('subscriber', {}).get('id')
        message_text = data.get('message', {}).get('text')
        
        if not customer_id or not message_text:
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        # Get customer history
        customer_history = await Database.get_customer_history(customer_id)
        
        # Analyze message using AI
        analysis = await ai_service.analyze_message(
            message=message_text,
            context=customer_history
        )
        
        # Generate response
        response = await ai_service.generate_response(
            message=message_text,
            analysis=analysis,
            customer_history=customer_history
        )
        
        # Save message to database
        await Database.save_chat_message(
            customer_id=customer_id,
            message={
                "content": message_text,
                "timestamp": datetime.now(),
                "is_from_customer": True
            }
        )
        
        # Save response to database
        await Database.save_chat_message(
            customer_id=customer_id,
            message={
                "content": response,
                "timestamp": datetime.now(),
                "is_from_customer": False
            }
        )
        
        # Return response to ManyChat
        return {
            "messages": [
                {
                    "type": "text",
                    "text": response
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
