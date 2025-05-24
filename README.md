# نظام دعم عملاء Instagram المدعوم بالذكاء الاصطناعي

نظام متكامل للرد الآلي على استفسارات العملاء عبر Instagram باستخدام الذكاء الاصطناعي.

## المميزات الرئيسية

- ✨ ربط مباشر مع Instagram عبر ManyChat
- 🤖 ردود ذكية باستخدام GPT-4
- 🎯 تحليل نوايا العملاء وتوجيه الردود المناسبة
- 🗣️ دعم الرسائل الصوتية (تحويل الصوت إلى نص)
- 📊 تخزين وتتبع الطلبات في Google Sheets
- 🚚 ربط مع شركات الشحن (RGS, Aramex, AyMakan)
- 📱 لوحة تحكم لمراقبة المحادثات
- 🌐 دعم اللغتين العربية والإنجليزية
- 📝 نظام تعلّم ذاتي للتحسين المستمر

## المتطلبات الأساسية

1. Python 3.8+
2. Docker Desktop
3. حساب Instagram للأعمال
4. حساب ManyChat
5. حساب Google Cloud (للـ Sheets API)
6. حسابات API لشركات الشحن

## التثبيت

1. نسخ المستودع:
\`\`\`bash
git clone https://github.com/yourusername/instagram-ai-support.git
cd instagram-ai-support
\`\`\`

2. إنشاء البيئة الافتراضية:
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate   # Windows
\`\`\`

3. تثبيت المتطلبات:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. إعداد ملف البيئة:
- نسخ \`.env.example\` إلى \`.env\`
- تعبئة المتغيرات المطلوبة

## التشغيل

1. تشغيل الخادم:
\`\`\`bash
uvicorn src.app:app --reload
\`\`\`

2. فتح Swagger UI:
\`http://localhost:8000/docs\`

## نقاط النهاية API

- \`POST /webhook/manychat\`: استقبال الرسائل من ManyChat
- \`POST /voice-message\`: معالجة الرسائل الصوتية
- \`GET /track-order/{tracking_number}\`: تتبع حالة الطلب
- \`GET /customer-history/{phone}\`: عرض سجل طلبات العميل
- \`POST /update-order-status\`: تحديث حالة الطلب

## الهيكل التنظيمي

\`\`\`
instagram-ai-support/
├── src/
│   ├── core/
│   │   ├── ai_engine.py
│   │   └── customer_files.py
│   ├── integrations/
│   │   ├── manychat.py
│   │   ├── sheets_manager.py
│   │   └── shipping_manager.py
│   └── app.py
├── tests/
├── .env
├── requirements.txt
└── README.md
\`\`\`

## المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. عمل Fork للمشروع
2. إنشاء فرع للميزة: \`git checkout -b feature/amazing-feature\`
3. عمل Commit للتغييرات: \`git commit -m 'إضافة ميزة رائعة'\`
4. رفع التغييرات: \`git push origin feature/amazing-feature\`
5. فتح طلب Pull Request

## الترخيص

هذا المشروع مرخص تحت [MIT License](LICENSE).
