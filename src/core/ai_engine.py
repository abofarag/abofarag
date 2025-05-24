import os
from typing import Dict, List, Optional
import openai
from datetime import datetime
import weaviate

class AIEngine:
    def __init__(self):
        # تهيئة OpenAI
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4-1106-preview')
        self.brand_name = os.getenv('BRAND_NAME', 'Onestock')
        self.brand_voice = os.getenv('BRAND_VOICE', 'professional and friendly')
        self.default_language = os.getenv('DEFAULT_LANGUAGE', 'ar')
        openai.api_key = self.api_key
        
        # تهيئة Weaviate
        self.weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv('WEAVIATE_URL'),
            auth_credentials=weaviate.auth.AuthApiKey(api_key=os.getenv('WEAVIATE_API_KEY'))
        )
    
    async def analyze_message(self, message: str, customer_id: str = None) -> Dict:
        """تحليل رسالة العميل وتحديد النية والمشاعر"""
        # البحث عن سياق العميل السابق
        context = await self._get_customer_context(customer_id) if customer_id else {}
        
        system_prompt = f"""أنت موظف خدمة عملاء محترف في {self.brand_name}. 
        قم بتحليل رسالة العميل التالية وإرجاع:
        1. النية (استفسار، شكوى، حالة_طلب، طلب_جديد، إلخ)
        2. المشاعر (إيجابي، سلبي، محايد)
        3. اللغة (ar, en)
        4. المعلومات المهمة المستخرجة (أرقام الطلبات، أسماء المنتجات، إلخ)
        
        معلومات إضافية عن العميل:
        {context}
        """
        
        try:
            response = await openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                response_format={ "type": "json_object" }
            )
            analysis = response.choices[0].message.content
            
            # حفظ التحليل في Weaviate
            if customer_id:
                await self._store_interaction(customer_id, message, analysis)
            
            return analysis
        except Exception as e:
            print(f"Error analyzing message: {e}")
            return {
                "intent": "unknown",
                "sentiment": "neutral",
                "language": self.default_language,
                "key_info": {}
            }
    
    async def _store_interaction(self, customer_id: str, message: str, analysis: Dict) -> None:
        """تخزين تفاعل العميل في Weaviate"""
        try:
            # إنشاء كائن التفاعل
            interaction_object = {
                "customer_id": customer_id,
                "message": message,
                "intent": analysis.get('intent'),
                "sentiment": analysis.get('sentiment'),
                "language": analysis.get('language'),
                "key_info": analysis.get('key_info'),
                "timestamp": datetime.now().isoformat()
            }
            
            # تخزين في Weaviate
            self.weaviate_client.data_object.create(
                "CustomerInteraction",
                interaction_object
            )
        except Exception as e:
            print(f"Error storing interaction in Weaviate: {e}")
    
    async def _get_customer_context(self, customer_id: str) -> Dict:
        """استرجاع سياق العميل من Weaviate"""
        try:
            # البحث عن آخر تفاعلات العميل
            query = self.weaviate_client.query.get(
                "CustomerInteraction", ["message", "intent", "sentiment", "key_info", "timestamp"]
            ).with_where({
                "path": ["customer_id"],
                "operator": "Equal",
                "valueString": customer_id
            }).with_limit(5).do()
            
            interactions = query.get('data', {}).get('Get', {}).get('CustomerInteraction', [])
            
            if not interactions:
                return {}
            
            # تحليل التفاعلات السابقة
            context = {
                "last_interaction": interactions[0].get('timestamp'),
                "common_intents": [],
                "recent_products": [],
                "sentiment_history": []
            }
            
            for interaction in interactions:
                if interaction.get('intent'):
                    context['common_intents'].append(interaction['intent'])
                if interaction.get('sentiment'):
                    context['sentiment_history'].append(interaction['sentiment'])
                if interaction.get('key_info', {}).get('products'):
                    context['recent_products'].extend(interaction['key_info']['products'])
            
            # إزالة التكرارات
            context['common_intents'] = list(set(context['common_intents']))
            context['recent_products'] = list(set(context['recent_products']))
            
            return context
        except Exception as e:
            print(f"Error getting customer context from Weaviate: {e}")
            return {}
    
    async def generate_response(self, 
                              message: str, 
                              customer_id: str,
                              analysis: Dict) -> str:
        """توليد رد مناسب للعميل"""
        # الحصول على سياق العميل
        context = await self._get_customer_context(customer_id)
        
        system_prompt = f"""أنت موظف خدمة عملاء محترف في {self.brand_name}.
        
        إرشادات مهمة:
        1. استخدم نفس لغة العميل (عربي أو إنجليزي)
        2. كن مختصراً ومفيداً
        3. إذا لم تكن لديك معلومات معينة، اطلبها بأدب
        4. لحالة الطلب، قم دائماً بتضمين معلومات التتبع إذا كانت متوفرة
        5. أظهر التعاطف في حالة الشكاوى
        
        معلومات عن العميل:
        - آخر تفاعل: {context.get('last_interaction', 'لا يوجد')}
        - النوايا السابقة: {', '.join(context.get('common_intents', []))}
        - المنتجات الأخيرة: {', '.join(context.get('recent_products', []))}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        try:
            response = await openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return "عذراً، سأقوم بتحويلك إلى زميلي للمساعدة."
    
    async def transcribe_voice(self, audio_file_path: str) -> str:
        """تحويل الرسالة الصوتية إلى نص"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = await openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=self.default_language
                )
            return transcript.text
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""
