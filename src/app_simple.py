from fastapi import FastAPI, HTTPException
from typing import Dict
import os
from dotenv import load_dotenv
from src.core.memory_store import MemoryStore

load_dotenv()

app = FastAPI()
store = MemoryStore()

@app.get("/")
def read_root():
    """فحص حالة الخادم"""
    try:
        return {"message": "Instagram AI Support API", "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customer")
async def create_customer(customer: Dict):
    """إنشاء عميل جديد"""
    try:
        if not customer.get('phone'):
            raise HTTPException(status_code=400, detail="Missing phone number")
        if not customer.get('name'):
            raise HTTPException(status_code=400, detail="Missing customer name")
            
        customer_id = store.create_customer(
            phone=customer['phone'],
            name=customer['name'],
            email=customer.get('email', '')
        )
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "message": "Customer created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/manychat")
async def manychat_webhook(data: Dict):
    """معالجة الويب هوك من ManyChat"""
    try:
        if not data.get('subscriber'):
            raise HTTPException(status_code=400, detail="Missing subscriber data")
            
        subscriber = data['subscriber']
        customer_id = subscriber.get('id')
        if not customer_id:
            raise HTTPException(status_code=400, detail="Missing subscriber ID")
            
        # التحقق من وجود العميل أو إنشاء واحد جديد
        customer = store.get_customer(f"CUST_{customer_id}")
        if not customer:
            name = subscriber.get('name', 'Unknown')
            customer_id = store.create_customer(
                phone=customer_id,
                name=name
            )
        
        # معالجة الرسالة
        if data.get('text'):
            store.add_message(customer_id, data['text'])
            return {
                "status": "success",
                "response": "تم استلام رسالتك",
                "analysis": {
                    "sentiment": "neutral",
                    "intent": "general"
                }
            }
            
        return {"status": "success", "message": "Webhook received"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
