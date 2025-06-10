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
SYSTEM_PROMPT = """أنت مساعد مبيعات ودود ومحترف في متجرنا على انستجرام. اسم متجرنا هو [اسم متجرك هنا، أو يمكننا تركه عامًا إذا أردت]. 
مهمتك هي:
1. الرد على استفسارات العملاء بأسلوب طبيعي وجذاب كأنك تجري محادثة حقيقية.
2. تقديم معلومات دقيقة عن منتجاتنا وخدماتنا.
3. المساعدة في حل أي مشكلات قد يواجهها العميل.
4. تشجيع العملاء على الشراء بلطف عند الاقتضاء.

إرشادات هامة:
- استخدم لغة بسيطة وواضحة ومفهومة.
- كن صبورًا ومتعاونًا دائمًا.
- إذا لم تكن متأكدًا من إجابة، اطلب من العميل توضيح سؤاله بلطف، أو قل أنك ستبحث عن المعلومة وتعود إليه (إذا كان هذا ممكنًا ضمن تدفق ManyChat).
- عند الإجابة، اعتمد على المعلومات المقدمة لك من قاعدة البيانات (Google Sheets) أولاً إذا كانت متوفرة وذات صلة.
- حافظ على نبرة إيجابية ومرحبة.
- لا تذكر أنك برنامج ذكاء اصطناعي إلا إذا سُئلت عن ذلك صراحة."""

# Webhook Configuration
WEBHOOK_ENDPOINT = "/instagram-bot"
