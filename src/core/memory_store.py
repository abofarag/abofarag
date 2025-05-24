from typing import Dict, Optional
from datetime import datetime
import time

class MemoryStore:
    def __init__(self):
        self.customers = {}
        self.messages = []
    
    def create_customer(self, phone: str, name: str, email: str = "", instagram: str = "") -> str:
        """إنشاء عميل جديد"""
        customer_id = f"CUST_{phone}"
        
        if customer_id not in self.customers:
            self.customers[customer_id] = {
                "customer_id": customer_id,
                "phone": phone,
                "name": name,
                "email": email,
                "instagram": instagram,
                "created_at": datetime.now().isoformat()
            }
        
        return customer_id
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """الحصول على بيانات العميل"""
        return self.customers.get(customer_id)
    
    def add_message(self, customer_id: str, message: str) -> bool:
        """إضافة رسالة جديدة"""
        if customer_id not in self.customers:
            return False
            
        self.messages.append({
            "customer_id": customer_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        return True
    
    def get_customer_messages(self, customer_id: str) -> list:
        """الحصول على رسائل العميل"""
        return [
            msg for msg in self.messages 
            if msg["customer_id"] == customer_id
        ]
