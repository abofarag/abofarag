from typing import Dict, Any, Optional, List
import openai
from datetime import datetime
import pytz
from .sheets_manager import GoogleSheetsManager

class Memory:
    def __init__(self, max_messages: int = 10):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.max_messages = max_messages
    
    def add_message(self, contact_id: str, role: str, content: str):
        if contact_id not in self.conversations:
            self.conversations[contact_id] = []
        
        self.conversations[contact_id].append({"role": role, "content": content})
        
        # Keep only last N messages
        if len(self.conversations[contact_id]) > self.max_messages:
            self.conversations[contact_id] = self.conversations[contact_id][-self.max_messages:]
    
    def get_conversation(self, contact_id: str) -> List[Dict[str, str]]:
        return self.conversations.get(contact_id, [])

class AIAgent:
    def __init__(self, openai_api_key: str, sheets_manager: GoogleSheetsManager):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.sheets_manager = sheets_manager
        self.memory = Memory()
        self.system_message = """مهمتك هي الإجابة بدقة ووضوح على أسئلة العملاء حول منتج 'جاسترو زيرو'.

قواعد أساسية:
1. للأسئلة العامة (التحية): اجب بشكل طبيعي
2. للأسئلة عن المنتج: استخدم أداة Google Sheets Tool دائماً
3. ابحث باستخدام: 'جاسترو زيرو - [نوع المعلومة]'

ملاحظات مهمة:
- كن دقيقاً في إجاباتك
- اجعل ردودك مختصرة ومفيدة
- استخدم لغة مهذبة ومحترفة
- إذا لم تجد معلومة، اطلب من العميل التوضيح"""

    async def process_message(self, user_input: str, contact_id: str) -> Dict[str, Any]:
        print(f"[AIAgent] process_message called with user_input: {user_input}, contact_id: {contact_id}")
        
        # 1. أولاً نتحقق من الأسئلة المتعلقة بالسعر
        price_keywords = ['سعر', 'كم', 'تكلفة', 'ريال', 'دينار', 'درهم', 'جنيه', 'دولار', 'كلف', 'ثمن', 'قيمة']
        query_lower = user_input.lower()
        is_price_query = any(keyword in query_lower for keyword in price_keywords)
        
        if is_price_query and ('جاسترو' in query_lower or 'زيرو' in query_lower):
            # إذا كان سؤال عن السعر، نرجع رد مباشر دون الحاجة للطلب من ChatGPT
            print(f"[AIAgent] Price question detected, returning direct answer")
            bot_response = "سعر منتج جاسترو زيرو هو 250 ريال."
            
            # تسجيل التفاعل
            print(f"[AIAgent] Logging interaction with direct price answer")
            try:
                await self.log_interaction(contact_id, user_input, bot_response)
                print("[AIAgent] Interaction logged successfully")
            except Exception as e:
                print(f"[AIAgent] Error logging interaction: {str(e)}")
                
            return {"output": bot_response}
        
        # 2. بحث في قاعدة المعرفة
        knowledge = await self.sheets_manager.search_knowledge_base(user_input)
        print(f"[AIAgent] Knowledge base result: {knowledge}")
        
        # 3. إذا وجدنا نتيجة من قاعدة المعرفة واضحة ومباشرة
        if knowledge and knowledge.startswith('ج:'):
            # إذا كانت الإجابة مباشرة من قاعدة المعرفة
            bot_response = knowledge.replace('ج: ', '')
            try:
                await self.log_interaction(contact_id, user_input, bot_response)
                print("[AIAgent] Interaction with direct knowledge answer logged successfully")
            except Exception as e:
                print(f"[AIAgent] Error logging interaction: {str(e)}")
                
            return {"output": bot_response}

        # 4. طلب من ChatGPT
        system_msg = self.system_message + "\n\nملاحظة مهمة: استخدم المعلومات من قاعدة البيانات إذا كانت متوفرة."
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"العميل يقول: {user_input}\n\nمعلومات من قاعدة البيانات:\n{knowledge}"}
        ]
        print(f"[AIAgent] Messages sent to OpenAI: {messages}")

        # إنشاء client OpenAI بطريقة بديلة دون استخدام proxies
        try:
            import httpx
            # استخدام Client بدون proxies
            http_client = httpx.AsyncClient()
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key, http_client=http_client)
            
            print(f"[AIAgent] Using custom httpx client without proxies: {httpx.__version__}")
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
        except Exception as e:
            print(f"[AIAgent] Error creating client: {str(e)}")
            # الطريقة العادية كخطة بديلة
            response = await openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

        bot_response = response.choices[0].message.content
        print(f"[AIAgent] ChatGPT response: {bot_response}")

        # Log interaction - محاولة منفصلة لضمان التسجيل
        try:
            await self.log_interaction(contact_id, user_input, bot_response)
            print("[AIAgent] Interaction logged successfully")
        except Exception as e:
            print(f"[AIAgent] Error logging interaction: {str(e)}")
        
        return {"output": bot_response}

    async def log_interaction(self, contact_id: str, user_question: str, bot_answer: str):
        dubai_tz = pytz.timezone('Asia/Dubai')
        timestamp = datetime.now(dubai_tz).strftime('%d/%m/%Y %H:%M:%S')
        
        await self.sheets_manager.log_interaction(
            timestamp=timestamp,
            contact_id=contact_id,
            user_question=user_question,
            bot_answer=bot_answer
        )
