pip install -r requirements.txt
python -m uvicorn src.app:app --reload --host 127.0.0.1 --port 12345
import os
from dotenv import load_dotenv
import requests
import json

# تحميل المتغيرات البيئية
load_dotenv()

BASE_URL = 'http://127.0.0.1:12345'

def test_webhook_message():
    # محاكاة رسالة من عميل
    data = {
        "type": "message",
        "subscriber": {
            "id": "123456789",
            "first_name": "محمد",
            "last_name": "أحمد"
        },
        "message": {
            "text": "مرحباً، أريد الاستفسار عن المنتج XYZ"
        }
    }
    
    response = requests.post(f"{BASE_URL}/webhook/manychat", json=data)
    print("\nاختبار webhook/manychat:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_process_message():
    # اختبار معالجة رسالة مباشرة
    data = {
        "message": "كم سعر المنتج ABC؟"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/customer/123456789/message",
        json=data
    )
    print("\nاختبار process_message:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_get_customer_history():
    # اختبار استرجاع تاريخ العميل
    response = requests.get(f"{BASE_URL}/api/customer/123456789/history")
    print("\nاختبار get_customer_history:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

def test_get_customer_context():
    # اختبار استرجاع سياق العميل
    response = requests.get(f"{BASE_URL}/api/customer/123456789/context")
    print("\nاختبار get_customer_context:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

if __name__ == '__main__':
    print("بدء اختبارات النظام...\n")
    
    # تشغيل الاختبارات
    test_webhook_message()
    test_process_message()
    test_get_customer_history()
    test_get_customer_context()
