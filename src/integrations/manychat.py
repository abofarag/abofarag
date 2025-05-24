import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime

class ManyChatAPI:
    def __init__(self):
        self.api_key = os.getenv('MANYCHAT_API_KEY')
        self.page_id = os.getenv('MANYCHAT_PAGE_ID')
        self.flow_id = os.getenv('MANYCHAT_FLOW_ID')
        self.base_url = 'https://api.manychat.com'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """إجراء طلب إلى ManyChat API"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            else:
                response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"ManyChat API error: {e}")
            return {}
            
    def send_message(self, subscriber_id: str, message: str) -> Dict:
        """إرسال رسالة إلى مشترك"""
        endpoint = f"{self.base_url}/fb/sending/sendContent"
        
        data = {
            "subscriber_id": subscriber_id,
            "data": {
                "version": "v2",
                "content": {
                    "messages": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            }
        }
        
        try:
            response = requests.post(endpoint, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return {"status": "error", "message": str(e)}
    
    def trigger_flow(self, subscriber_id: str, flow_ns: str) -> Dict:
        """تشغيل تدفق لمشترك"""
        endpoint = f"{self.base_url}/fb/sending/triggerFlow"
        
        data = {
            "subscriber_id": subscriber_id,
            "flow_ns": flow_ns
        }
        
        try:
            response = requests.post(endpoint, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error triggering flow: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_subscriber_info(self, subscriber_id: str) -> Dict:
        """الحصول على معلومات المشترك"""
        endpoint = f"{self.base_url}/fb/subscriber/getInfo"
        
        params = {
            "subscriber_id": subscriber_id
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting subscriber info: {e}")
            return {"status": "error", "message": str(e)}

class ManyChatWebhookHandler:
    def __init__(self, customer_manager, ai_engine):
        self.api_key = os.getenv('MANYCHAT_API_KEY')
        self.manychat_api = ManyChatAPI(self.api_key)
        self.customer_manager = customer_manager
        self.ai_engine = ai_engine
    
    async def handle_message(self, data: Dict) -> Dict:
        """معالجة رسالة واردة من ManyChat"""
        try:
            subscriber_id = data.get('subscriber', {}).get('id')
            message = data.get('message', {}).get('text', '')
            
            if not subscriber_id or not message:
                return {
                    "status": "error",
                    "message": "Missing subscriber_id or message"
                }
            
            # الحصول على معلومات المشترك
            subscriber_info = self.manychat_api.get_subscriber_info(subscriber_id)
            
            # إنشاء أو تحديث ملف العميل
            customer_data = {
                "subscriber_id": subscriber_id,
                "name": subscriber_info.get('first_name', '') + ' ' + subscriber_info.get('last_name', ''),
                "instagram_username": subscriber_info.get('instagram_username'),
                "last_message": message,
                "last_interaction": datetime.now().isoformat()
            }
            
            # تحليل الرسالة
            analysis = await self.ai_engine.analyze_message(message, subscriber_id)
            
            # توليد الرد
            response_text = await self.ai_engine.generate_response(message, subscriber_id, analysis)
            
            # إرسال الرد
            response = self.manychat_api.send_message(subscriber_id, response_text)
            
            # تحديث ملف العميل
            customer_data["last_analysis"] = analysis
            await self.customer_manager.create_customer_file(subscriber_id, customer_data)
            
            return {"status": "success", "data": response}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def handle_flow_trigger(self, data: Dict) -> Dict:
        """معالجة تشغيل تدفق من ManyChat"""
        try:
            subscriber_id = data.get('subscriber', {}).get('id')
            flow_ns = data.get('flow', {}).get('ns')
            
            if not subscriber_id or not flow_ns:
                return {"status": "error", "message": "Missing subscriber ID or flow NS"}
            
            # تشغيل الـ flow
            response = self.api.send_flow(subscriber_id, flow_ns)
            
            return {
                "status": "success",
                "response": response
            }
            
        except Exception as e:
            print(f"Error handling flow trigger: {e}")
            return {"status": "error", "message": str(e)}
