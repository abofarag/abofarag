import os
import weaviate
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

def create_schema(client: weaviate.Client) -> None:
    """إنشاء مخطط Weaviate للتفاعلات"""
    
    # مخطط تفاعلات العملاء
    customer_interaction_class = {
        "class": "CustomerInteraction",
        "description": "تفاعلات العملاء وتحليلاتها",
        "vectorizer": "text2vec-openai",  # استخدام OpenAI لتحويل النص إلى متجهات
        "moduleConfig": {
            "text2vec-openai": {
                "model": "ada",
                "modelVersion": "002",
                "type": "text"
            }
        },
        "properties": [
            {
                "name": "customer_id",
                "description": "معرف العميل",
                "dataType": ["string"]
            },
            {
                "name": "message",
                "description": "نص الرسالة",
                "dataType": ["text"],
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": False,
                        "vectorizePropertyName": False
                    }
                }
            },
            {
                "name": "intent",
                "description": "قصد العميل",
                "dataType": ["string"]
            },
            {
                "name": "sentiment",
                "description": "مشاعر العميل",
                "dataType": ["string"]
            },
            {
                "name": "timestamp",
                "description": "وقت التفاعل",
                "dataType": ["date"]
            },
            {
                "name": "response",
                "description": "رد النظام",
                "dataType": ["text"],
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": False,
                        "vectorizePropertyName": False
                    }
                }
            },
            {
                "name": "context",
                "description": "سياق التفاعل",
                "dataType": ["text"],
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": False,
                        "vectorizePropertyName": False
                    }
                }
            }
        ]
    }
    
    try:
        client.schema.create_class(customer_interaction_class)
        print("تم إنشاء المخطط بنجاح")
    except Exception as e:
        if "already exists" in str(e):
            print("المخطط موجود بالفعل")
        else:
            print(f"خطأ في إنشاء المخطط: {e}")

def init_weaviate() -> weaviate.Client:
    """تهيئة اتصال Weaviate"""
    try:
        # إنشاء اتصال Weaviate مع تكوين OpenAI
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
            headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
        )
        
        # التحقق من الاتصال
        if not client.is_ready():
            raise Exception("Weaviate is not ready")
        
        # إنشاء المخطط إذا لم يكن موجوداً
        create_schema(client)
        
        return client
    except Exception as e:
        print(f"Error initializing Weaviate: {e}")
        return None
