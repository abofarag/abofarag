import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# تحميل المتغيرات البيئية
load_dotenv()

BASE_URL = 'http://127.0.0.1:12345'

def test_webhook_message():
    """اختبار إرسال رسالة عبر webhook"""
    try:
        data = {
            "subscriber": {
                "id": "123456789",
                "name": "محمد أحمد"
            },
            "text": "مرحباً، كيف حالك؟"
        }
        
        print("\nاختبار إرسال رسالة عبر webhook:")
        response = requests.post(f"{BASE_URL}/webhook/manychat", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")
        return False

def test_customer_creation():
    """اختبار إنشاء عميل جديد"""
    try:
        data = {
            "phone": "123456789",
            "name": "محمد أحمد",
            "email": "test@example.com"
        }
        
        print("\nاختبار إنشاء عميل جديد:")
        response = requests.post(f"{BASE_URL}/api/customer", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"خطأ في إنشاء العميل: {e}")
        return False

def test_webhook_no_subscriber():
    """اختبار إرسال رسالة بدون بيانات المشترك"""
    try:
        data = {
            "text": "مرحباً"
        }
        
        print("\nاختبار إرسال رسالة بدون بيانات المشترك:")
        response = requests.post(f"{BASE_URL}/webhook/manychat", json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 400  # يجب أن يفشل
    except Exception as e:
        print(f"خطأ في الاختبار: {e}")
        return False

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("بدء اختبارات ManyChat...\n")
    
    tests = [
        ("إنشاء عميل جديد", test_customer_creation),
        ("إرسال رسالة عبر webhook", test_webhook_message),
        ("إرسال رسالة بدون بيانات المشترك", test_webhook_no_subscriber)
    ]
    
    success_count = 0
    for test_name, test_func in tests:
        print(f"\n=== اختبار: {test_name} ===")
        try:
            if test_func():
                print(f"✅ نجح الاختبار: {test_name}")
                success_count += 1
            else:
                print(f"❌ فشل الاختبار: {test_name}")
        except Exception as e:
            print(f"❌ فشل الاختبار: {test_name}")
            print(f"الخطأ: {e}")
    
    print(f"\nالنتيجة النهائية: {success_count}/{len(tests)} اختبارات ناجحة")
    return success_count == len(tests)

if __name__ == "__main__":
    # التأكد من أن الخادم يعمل
    try:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("❌ الخادم لا يستجيب بشكل صحيح!")
            exit(1)
    except Exception as e:
        print("❌ لا يمكن الاتصال بالخادم! تأكد من تشغيله على المنفذ 12345")
        print(f"الخطأ: {e}")
        exit(1)
    
    # تشغيل الاختبارات
    if run_all_tests():
        print("\n✨ جميع الاختبارات نجحت!")
        exit(0)
    else:
        print("\n⚠️ بعض الاختبارات فشلت")
        exit(1)
