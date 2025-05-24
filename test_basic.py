import os
from dotenv import load_dotenv
import requests
import json
import time
from datetime import datetime

# تحميل المتغيرات البيئية
load_dotenv()

BASE_URL = 'http://127.0.0.1:12345'

def test_server_status():
    """اختبار حالة الخادم"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print("\nاختبار حالة الخادم:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"خطأ في الاتصال بالخادم: {e}")
        return False

def test_create_customer():
    """اختبار إنشاء عميل جديد"""
    try:
        data = {
            "phone": "123456789",
            "name": "محمد أحمد",
            "email": "test@example.com"
        }
        
        response = requests.post(f"{BASE_URL}/api/customer", json=data)
        print("\nاختبار إنشاء عميل:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 201
    except Exception as e:
        print(f"خطأ في إنشاء العميل: {e}")
        return False

def test_simple_message():
    """اختبار إرسال رسالة بسيطة"""
    try:
        data = {
            "type": "message",
            "subscriber": {
                "id": "123456789",
                "name": "محمد أحمد"
            },
            "text": "مرحباً"
        }
        
        response = requests.post(f"{BASE_URL}/webhook/manychat", json=data)
        print("\nاختبار إرسال رسالة:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")
        return False

if __name__ == '__main__':
    print("بدء الاختبارات الأساسية...\n")
    
    # اختبار الخادم
    if not test_server_status():
        print("فشل الاتصال بالخادم!")
        exit(1)
    
    # اختبار إنشاء عميل
    if not test_create_customer():
        print("فشل إنشاء العميل!")
        exit(1)
    
    # اختبار إرسال رسالة
    if not test_simple_message():
        print("فشل إرسال الرسالة!")
        exit(1)
    
    print("\nتم إكمال جميع الاختبارات بنجاح!")
