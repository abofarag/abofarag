from openai import AsyncOpenAI
from ..core.config import settings
from typing import Dict, Any

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def analyze_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze customer message and determine intent"""
        system_prompt = """
        أنت مساعد خدمة عملاء محترف. مهمتك تحليل رسائل العملاء وتحديد:
        1. نوع الرسالة (استفسار، طلب، شكوى، الخ)
        2. المنتجات المذكورة
        3. المعلومات المهمة
        4. الحالة النفسية للعميل
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        if context:
            messages.insert(1, {
                "role": "assistant",
                "content": f"معلومات سابقة عن العميل: {str(context)}"
            })
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    async def generate_response(self, 
                              message: str, 
                              analysis: Dict[str, Any],
                              customer_history: Dict[str, Any] = None) -> str:
        """Generate appropriate response based on message analysis"""
        system_prompt = """
        أنت مساعد خدمة عملاء محترف ولطيف. عليك:
        1. الرد بأسلوب ودي ومهني
        2. تقديم معلومات دقيقة
        3. توجيه العميل للخطوات التالية
        4. استخدام الإيموجي المناسبة 🌟
        """
        
        context = f"""
        تحليل الرسالة: {str(analysis)}
        """
        
        if customer_history:
            context += f"\nسجل العميل: {str(customer_history)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"الرسالة: {message}\n{context}"}
        ]
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.8
        )
        
        return response.choices[0].message.content
