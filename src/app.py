import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict, Optional
import json

from src.core.customer_files import CustomerFileManager
from src.core.ai_engine import AIEngine
from src.core.weaviate_schema import init_weaviate
from src.integrations.manychat import ManyChatWebhookHandler
from src.integrations.sheets_manager import GoogleSheetsManager
from src.integrations.shipping_manager import ShippingManager
from .api import webhook, health

load_dotenv()

app = FastAPI(title="Instagram AI Support API")

# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تهيئة المكونات
weaviate_client = init_weaviate()
# تهيئة المديرين
customer_manager = CustomerFileManager(weaviate_client)
ai_engine = AIEngine()
sheets_manager = GoogleSheetsManager()
shipping_manager = ShippingManager()
webhook_handler = ManyChatWebhookHandler(customer_manager, ai_engine)

app.include_router(webhook.router)
app.include_router(health.router)

@app.get("/")
def read_root():
    try:
        return {"message": "Instagram AI Support API", "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customer")
async def create_customer(customer: Dict):
    """إنشاء عميل جديد"""
    try:
        # التحقق من وجود البيانات المطلوبة
        if not customer.get('phone'):
            raise HTTPException(status_code=400, detail="Missing phone number")
        if not customer.get('name'):
            raise HTTPException(status_code=400, detail="Missing customer name")
            
        # إنشاء ملف العميل
        customer_id = customer_manager.create_customer_file(
            phone=customer['phone'],
            name=customer['name'],
            email=customer.get('email', ''),
            instagram=customer.get('instagram', '')
        )
        
        if not customer_id:
            raise HTTPException(status_code=500, detail="Failed to create customer")
            
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
        # التحقق من وجود البيانات المطلوبة
        if not data.get('subscriber'):
            raise HTTPException(status_code=400, detail="Missing subscriber data")
            
        subscriber = data['subscriber']
        customer_id = subscriber.get('id')
        if not customer_id:
            raise HTTPException(status_code=400, detail="Missing subscriber ID")
            
        # التحقق من وجود ملف للعميل أو إنشاء واحد جديد
        customer = customer_manager.get_customer_file(customer_id, "customer_id")
        if not customer:
            name = subscriber.get('name', 'Unknown')
            customer_id = customer_manager.create_customer_file(
                phone=customer_id,  # نستخدم معرف العميل كرقم هاتف مؤقت
                name=name
            )
        
        # معالجة الرسالة
        if data.get('text'):
            # تحليل الرسالة
            analysis = await ai_engine.analyze_message(data['text'], customer_id)
            
            # إضافة التفاعل
            customer_manager.add_interaction(
                customer_id=customer_id,
                interaction_type="message",
                content=data['text'],
                sentiment=analysis.get('sentiment', ''),
                intent=analysis.get('intent', '')
            )
            
            # توليد الرد
            response = await ai_engine.generate_response(data['text'], customer_id, analysis)
            
            return {
                "status": "success",
                "response": response,
                "analysis": analysis
            }
            
        return {"status": "success", "message": "Webhook received"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-message")
async def process_voice_message(file: UploadFile = File(...)):
    """معالجة الرسائل الصوتية"""
    try:
        # حفظ الملف مؤقتاً
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # تحويل الصوت إلى نص
        text = await ai_engine.transcribe_voice(temp_file_path)
        
        # حذف الملف المؤقت
        os.remove(temp_file_path)
        
        if text:
            return {"status": "success", "text": text}
        else:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/track-order/{tracking_number}")
async def track_order(tracking_number: str, company: Optional[str] = None):
    """تتبع حالة الطلب"""
    try:
        # البحث عن الطلب في Google Sheets
        order = sheets_manager.search_order(tracking_number)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # استخدام شركة الشحن من الطلب إذا لم يتم تحديدها
        shipping_company = company or order.get('shipping_company')
        if not shipping_company:
            raise HTTPException(status_code=400, detail="Shipping company not specified")
        
        # تتبع الشحنة
        tracking_info = await shipping_manager.track_shipment(tracking_number, shipping_company)
        if tracking_info['status'] == 'error':
            raise HTTPException(status_code=400, detail=tracking_info['message'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customer/{customer_id}/history")
async def get_customer_history(customer_id: str):
    """الحصول على تاريخ تفاعلات العميل"""
    try:
        query = weaviate_client.query.get(
            "CustomerInteraction",
            ["message", "intent", "sentiment", "key_info", "timestamp"]
        ).with_where({
            "path": ["customer_id"],
            "operator": "Equal",
            "valueString": customer_id
        }).with_limit(10).do()
        
        interactions = query.get('data', {}).get('Get', {}).get('CustomerInteraction', [])
        return {"interactions": interactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customer/{customer_id}/context")
async def get_customer_context(customer_id: str):
    """الحصول على سياق العميل"""
    try:
        context = await ai_engine._get_customer_context(customer_id)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customer/{customer_id}/message")
async def process_message(customer_id: str, data: Dict):
    """معالجة رسالة من العميل"""
    try:
        message = data.get('message')
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
            
        # تحليل الرسالة
        analysis = await ai_engine.analyze_message(message, customer_id)
        
        # توليد الرد
        response = await ai_engine.generate_response(message, customer_id, analysis)
        
        return {
            "analysis": analysis,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/customer/{customer_id}/interaction")
async def add_interaction(customer_id: str, interaction: dict):
    """إضافة تفاعل جديد"""
    try:
        success = customer_manager.add_interaction(
            customer_id=customer_id,
            interaction_type=interaction.get('type', 'manual'),
            content=interaction.get('content', ''),
            sentiment=interaction.get('sentiment', ''),
            intent=interaction.get('intent', '')
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
            
        # تحليل سلوك العميل بعد التفاعل
        analysis = customer_manager.analyze_customer_behavior(customer_id)
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
