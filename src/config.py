from typing import Dict, Any

# ManyChat Configuration
MANYCHAT_API_KEY = "2971386:e12db6d5c717fbd13528627727e37665"
MANYCHAT_BASE_URL = "https://api.manychat.com"

# Google Sheets Configuration
SPREADSHEET_ID = "1io-F4wrAvYYl86-ZEreci4OhMCS4-oza3zi0-EqbsbY"
SHEET_NAME = "Q&A"
KNOWLEDGE_BASE_RANGE = "A2:F"  # Range for searching knowledge base
LOG_RANGE = "A:D"  # Range for logging interactions

# OpenAI Configuration
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 500
TEMPERATURE = 0.7

# Memory Configuration
MAX_MEMORY_MESSAGES = 10

# System Messages
SYSTEM_PROMPT = """مهمتك هي الإجابة بدقة ووضوح على أسئلة العملاء حول منتج 'جاسترو زيرو'.

قواعد أساسية:
1. للأسئلة العامة (التحية): اجب بشكل طبيعي
2. للأسئلة عن المنتج: استخدم أداة Google Sheets Tool دائماً
3. ابحث باستخدام: 'جاسترو زيرو - [نوع المعلومة]'

ملاحظات مهمة:
- كن دقيقاً في إجاباتك
- اجعل ردودك مختصرة ومفيدة
- استخدم لغة مهذبة ومحترفة
- إذا لم تجد معلومة، اطلب من العميل التوضيح"""

# Webhook Configuration
WEBHOOK_ENDPOINT = "/instagram-bot"
