import os
from dotenv import load_dotenv
import weaviate
from datetime import datetime

# تحميل المتغيرات البيئية
load_dotenv()

def test_weaviate_connection():
    """اختبار الاتصال بـ Weaviate Cloud"""
    try:
        # إنشاء اتصال Weaviate
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.getenv("WEAVIATE_URL"),
            auth_credentials=weaviate.auth.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
            headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
        )
        
        print("\n=== اختبار الاتصال بـ Weaviate Cloud ===")
        
        # التحقق من الاتصال
        if client.is_ready():
            print("✅ تم الاتصال بنجاح")
            
            # إضافة بيانات اختبار
            test_data = {
                "customer_id": "TEST_123",
                "message": "هذه رسالة اختبار",
                "intent": "test",
                "sentiment": "neutral",
                "timestamp": datetime.now().isoformat(),
                "response": "تم استلام رسالة الاختبار",
                "context": "اختبار الاتصال"
            }
            
            # إنشاء كائن في Weaviate
            try:
                client.data_object.create(
                    class_name="CustomerInteraction",
                    data_object=test_data
                )
                print("✅ تم إنشاء بيانات الاختبار بنجاح")
            except Exception as e:
                print(f"❌ خطأ في إنشاء بيانات الاختبار: {e}")
            
            # استرجاع البيانات
            try:
                result = client.query.get(
                    "CustomerInteraction", 
                    ["customer_id", "message"]
                ).with_where({
                    "path": ["customer_id"],
                    "operator": "Equal",
                    "valueString": "TEST_123"
                }).do()
                
                if result.get('data', {}).get('Get', {}).get('CustomerInteraction'):
                    print("✅ تم استرجاع بيانات الاختبار بنجاح")
                else:
                    print("❌ لم يتم العثور على بيانات الاختبار")
                    
            except Exception as e:
                print(f"❌ خطأ في استرجاع البيانات: {e}")
                
        else:
            print("❌ فشل الاتصال")
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")

if __name__ == "__main__":
    test_weaviate_connection()
