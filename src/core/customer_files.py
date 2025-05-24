import json
import time
from datetime import datetime
from pathlib import Path
import hashlib
import weaviate
from typing import Dict, List, Optional

class CustomerFileManager:
    def __init__(self, client: weaviate.WeaviateClient):
        self.client = client
        self.collection = self._ensure_collection()
        
    def _ensure_collection(self) -> None:
        """إنشاء مجموعة ملفات العملاء إذا لم تكن موجودة"""
        try:
            schema = {
                "class": "CustomerFile",
                "description": "Store customer information and history",
                "vectorizer": "none",
                "properties": [
                    # معرفات العميل
                    {"name": "customer_id", "dataType": ["string"]},
                    {"name": "phone", "dataType": ["string"]},
                    {"name": "customer_name", "dataType": ["string"]},
                    {"name": "customer_email", "dataType": ["string"]},
                    {"name": "instagram_handle", "dataType": ["string"]},
                    {"name": "instagram_id", "dataType": ["string"]},
                    
                    # بيانات التفاعل
                    {"name": "first_interaction", "dataType": ["int"]},
                    {"name": "last_interaction", "dataType": ["int"]},
                    {"name": "total_interactions", "dataType": ["int"]},
                    {"name": "interaction_frequency", "dataType": ["number"]},
                    
                    # بيانات الطلبات
                    {"name": "total_orders", "dataType": ["int"]},
                    {"name": "order_history", "dataType": ["string[]"]},
                    {"name": "avg_order_value", "dataType": ["number"]},
                    {"name": "preferred_products", "dataType": ["string[]"]},
                    
                    # تفضيلات وسلوك
                    {"name": "preferences", "dataType": ["string[]"]},
                    {"name": "notes", "dataType": ["string[]"]},
                    {"name": "chat_summary", "dataType": ["string"]},
                    {"name": "satisfaction_score", "dataType": ["number"]},
                    {"name": "satisfaction_history", "dataType": ["number[]"]},
                    
                    # تحليلات وتصنيفات
                    {"name": "customer_segment", "dataType": ["string"]},
                    {"name": "lifetime_value", "dataType": ["number"]},
                    {"name": "churn_risk", "dataType": ["number"]},
                    {"name": "tags", "dataType": ["string[]"]},
                    
                    # بيانات التعلم
                    {"name": "interaction_patterns", "dataType": ["string[]"]},
                    {"name": "sentiment_history", "dataType": ["string[]"]},
                    {"name": "intent_history", "dataType": ["string[]"]},
                    {"name": "learning_notes", "dataType": ["string[]"]},
                ]
            }
            
            try:
                self.client.schema.get("CustomerFile")
                print("Schema already exists")
            except Exception:
                self.client.schema.create_class(schema)
                print("Schema created successfully")
                
        except Exception as e:
            print(f"Error ensuring collection: {e}")
    
    def generate_customer_id(self, phone: str, name: str) -> str:
        """توليد معرف فريد للعميل بناءً على رقم هاتفه واسمه"""
        # إنشاء نص مركب من الهاتف والاسم
        combined = f"{phone}_{name}_{int(time.time())}"
        # إنشاء هاش SHA-256 وأخذ أول 8 أحرف منه
        hashed = hashlib.sha256(combined.encode()).hexdigest()[:8]
        # إضافة بادئة CUST للتمييز
        return f"CUST{hashed.upper()}"
    
    def create_customer_file(self, phone: str, name: str, email: str = "", instagram: str = "") -> str:
        """إنشاء ملف جديد للعميل"""
        customer_id = self.generate_customer_id(phone, name)
        current_time = int(time.time())
        
        customer_data = {
            "customer_id": customer_id,
            "phone": phone,
            "customer_name": name,
            "customer_email": email,
            "instagram_handle": instagram,
            "instagram_id": "",  # سيتم تحديثه لاحقاً
            
            # بيانات التفاعل
            "first_interaction": current_time,
            "last_interaction": current_time,
            "total_interactions": 0,
            "interaction_frequency": 0,
            
            # بيانات الطلبات
            "total_orders": 0,
            "order_history": [],
            "avg_order_value": 0,
            "preferred_products": [],
            
            # تفضيلات وسلوك
            "preferences": [],
            "notes": [],
            "chat_summary": "",
            "satisfaction_score": 0,
            "satisfaction_history": [],
            
            # تحليلات وتصنيفات
            "customer_segment": "جديد",
            "lifetime_value": 0,
            "churn_risk": 0.5,
            "tags": [],
            
            # بيانات التعلم
            "interaction_patterns": [],
            "sentiment_history": [],
            "intent_history": [],
            "learning_notes": []
        }
        
        try:
            self.client.data_object.create(
                class_name="CustomerFile",
                data_object=customer_data
            )
            return customer_id
        except Exception as e:
            print(f"Error creating customer file: {e}")
            return ""
    
    def get_customer_file(self, identifier: str, identifier_type: str = "phone") -> Optional[Dict]:
        """استرجاع ملف العميل باستخدام المعرف (رقم الهاتف أو معرف العميل)"""
        try:
            where_filter = {
                "path": [identifier_type],
                "operator": "Equal",
                "valueString": identifier
            }
            result = self.client.query.get(
                "CustomerFile", 
                ["customer_id", "phone", "customer_name", "customer_email", "instagram_handle", 
                 "instagram_id", "first_interaction", "last_interaction", "total_interactions", 
                 "interaction_frequency", "total_orders", "order_history", "avg_order_value", 
                 "preferred_products", "preferences", "notes", "chat_summary", "satisfaction_score", 
                 "satisfaction_history", "customer_segment", "lifetime_value", "churn_risk", 
                 "tags", "interaction_patterns", "sentiment_history", "intent_history", "learning_notes"]
            ).with_where(where_filter).do()
            
            if result and result["data"]["Get"]["CustomerFile"]:
                return result["data"]["Get"]["CustomerFile"][0]
            return None
            
        except Exception as e:
            print(f"Error getting customer file: {e}")
            return None
    
    def update_customer_file(self, customer_id: str, updates: Dict) -> bool:
        """تحديث ملف العميل"""
        try:
            # التحقق من وجود العميل
            customer = self.get_customer_file(customer_id, "customer_id")
            if not customer:
                return False
            
            # تحديث last_interaction تلقائياً
            updates["last_interaction"] = int(time.time())
            
            # حساب interaction_frequency
            time_diff = updates["last_interaction"] - customer["first_interaction"]
            days_diff = time_diff / (24 * 3600)  # تحويل الثواني إلى أيام
            updates["interaction_frequency"] = customer["total_interactions"] / days_diff if days_diff > 0 else 0
            
            # تحديث البيانات
            where_filter = {
                "path": ["customer_id"],
                "operator": "Equal",
                "valueString": customer_id
            }
            
            self.client.data_object.update(
                class_name="CustomerFile",
                where=where_filter,
                data_object=updates
            )
            return True
        except Exception as e:
            print(f"Error updating customer file: {e}")
            return False
    
    def add_interaction(self, customer_id: str, interaction_type: str, content: str, 
                       sentiment: str = "", intent: str = "") -> bool:
        """إضافة تفاعل جديد لملف العميل"""
        try:
            # الحصول على ملف العميل
            customer = self.get_customer_file(customer_id, "customer_id")
            if not customer:
                return False
            
            # تحديث التفاعلات
            interaction_patterns = customer.get("interaction_patterns", [])
            interaction_patterns.append(interaction_type)
            
            sentiment_history = customer.get("sentiment_history", [])
            if sentiment:
                sentiment_history.append(sentiment)
            
            intent_history = customer.get("intent_history", [])
            if intent:
                intent_history.append(intent)
            
            learning_notes = customer.get("learning_notes", [])
            learning_notes.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {content}")
            
            # تجهيز التحديثات
            updates = {
                "total_interactions": customer.get("total_interactions", 0) + 1,
                "interaction_patterns": interaction_patterns,
                "sentiment_history": sentiment_history,
                "intent_history": intent_history,
                "learning_notes": learning_notes,
                "last_interaction": int(time.time())
            }
            
            # تحديث ملف العميل
            self.client.data_object.update(
                class_name="CustomerFile",
                uuid=customer["id"],
                data_object=updates
            )
            return True
            
        except Exception as e:
            print(f"Error adding interaction: {e}")
            return False
    
    def analyze_customer_behavior(self, customer_id: str) -> Dict:
        """تحليل سلوك العميل وتحديث التصنيفات"""
        customer = self.get_customer_file(customer_id, "customer_id")
        if not customer:
            return {}
        
        # تحليل نمط التفاعل
        recent_sentiments = customer["sentiment_history"][-5:] if customer["sentiment_history"] else []
        recent_intents = customer["intent_history"][-5:] if customer["intent_history"] else []
        
        # حساب مخاطر فقدان العميل
        negative_sentiments = len([s for s in recent_sentiments if s == "negative"])
        complaint_intents = len([i for i in recent_intents if i == "complaint"])
        churn_risk = (negative_sentiments / len(recent_sentiments) if recent_sentiments else 0.5) + \
                     (complaint_intents / len(recent_intents) if recent_intents else 0.5) / 2
        
        # تحديد شريحة العميل
        if customer["total_orders"] == 0:
            segment = "جديد"
        elif customer["total_orders"] > 10 and customer["satisfaction_score"] >= 4:
            segment = "VIP"
        elif customer["total_orders"] > 5:
            segment = "منتظم"
        else:
            segment = "عادي"
        
        updates = {
            "customer_segment": segment,
            "churn_risk": churn_risk,
            "tags": self._generate_tags(customer)
        }
        
        self.update_customer_file(customer_id, updates)
        return updates
    
    def _generate_tags(self, customer: Dict) -> List[str]:
        """توليد الوسوم بناءً على بيانات العميل"""
        tags = []
        
        # وسوم الشريحة
        tags.append(f"شريحة_{customer['customer_segment']}")
        
        # وسوم التفاعل
        if customer["interaction_frequency"] > 0.5:  # أكثر من تفاعل كل يومين
            tags.append("تفاعل_عالي")
        
        # وسوم الرضا
        if customer["satisfaction_score"] >= 4:
            tags.append("راضي_جداً")
        elif customer["satisfaction_score"] <= 2:
            tags.append("غير_راضي")
            
        # وسوم المخاطر
        if customer["churn_risk"] > 0.7:
            tags.append("خطر_فقدان")
            
        return tags
