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
        # Search in knowledge base
        knowledge = await self.sheets_manager.search_knowledge_base(user_input)
        
        # Get conversation history
        conversation = self.memory.get_conversation(contact_id)
        
        # Build messages array
        messages = [
            {"role": "system", "content": self.system_message}
        ] + conversation + [
            {"role": "user", "content": f"سؤال العميل: {user_input}\n\nمعلومات من قاعدة البيانات:\n{knowledge}"}
        ]

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        bot_response = response.choices[0].message.content

        # Save to memory
        self.memory.add_message(contact_id, "user", user_input)
        self.memory.add_message(contact_id, "assistant", bot_response)

        # Log interaction
        await self.log_interaction(contact_id, user_input, bot_response)
        
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

    async def process_message(self, user_input: str, contact_id: str) -> Dict[str, Any]:
        # Search in knowledge base
        knowledge = await self.sheets_manager.search_knowledge_base(user_input)
        
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": f"العميل يقول: {user_input}\n\nمعلومات من قاعدة البيانات:\n{knowledge}"}
        ]

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        bot_response = response.choices[0].message.content

        # Log interaction
        await self.log_interaction(contact_id, user_input, bot_response)
        
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
