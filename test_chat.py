import os
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv
import time
import sys

# Set console encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Get credentials from environment variables
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

try:
    # Connect to Weaviate Cloud
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )

    # Delete collection if exists
    try:
        client.collections.delete("ChatMessage")
        client.collections.delete("CustomerFile")
    except Exception as e:
        print(f"[INFO] No collections to delete: {e}")
    except:
        pass

    # Create collection for chat messages
    print("\n1. Creating messages collection...")
    messages_collection = client.collections.create(
        name="ChatMessage",
        description="Store chat messages",
        vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none(),
        properties=[
            weaviate.classes.config.Property(name="content", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="sender", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="timestamp", data_type=weaviate.classes.config.DataType.INT),
            weaviate.classes.config.Property(name="sentiment", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="intent", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="order_id", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="customer_id", data_type=weaviate.classes.config.DataType.TEXT),
        ]
    )
    print("[SUCCESS] Messages collection created!")

    # Create customer files collection
    print("\n2. Creating customer files collection...")
    customer_collection = client.collections.create(
        name="CustomerFile",
        description="Store customer information and history",
        vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none(),
        properties=[
            weaviate.classes.config.Property(name="customer_id", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="phone", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="customer_name", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="customer_email", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="instagram_handle", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="total_orders", data_type=weaviate.classes.config.DataType.INT),
            weaviate.classes.config.Property(name="order_history", data_type=weaviate.classes.config.DataType.TEXT_ARRAY),
            weaviate.classes.config.Property(name="preferences", data_type=weaviate.classes.config.DataType.TEXT_ARRAY),
            weaviate.classes.config.Property(name="notes", data_type=weaviate.classes.config.DataType.TEXT_ARRAY),
            weaviate.classes.config.Property(name="chat_summary", data_type=weaviate.classes.config.DataType.TEXT),
            weaviate.classes.config.Property(name="last_interaction", data_type=weaviate.classes.config.DataType.INT),
            weaviate.classes.config.Property(name="satisfaction_score", data_type=weaviate.classes.config.DataType.NUMBER),
            weaviate.classes.config.Property(name="tags", data_type=weaviate.classes.config.DataType.TEXT_ARRAY),
        ]
    )
    print("[SUCCESS] Collection created!")

    # Add test customer files
    print("\n2. Adding test customer files...")
    customer_data = [
        {
            "customer_id": "CUST001",
            "phone": "+966501234567",
            "customer_name": "أحمد محمد",
            "customer_email": "ahmed@example.com",
            "instagram_handle": "@ahmed_fashion",
            "total_orders": 5,
            "order_history": ["123", "120", "115", "110", "105"],
            "preferences": ["يفضل التوصيل المسائي", "يفضل الدفع عند الاستلام"],
            "notes": ["عميل منتظم", "يهتم بالجودة العالية"],
            "chat_summary": "عميل منتظم يواجه مشكلة في تأخر الطلبات أحياناً",
            "last_interaction": int(time.time()),
            "satisfaction_score": 4.2,
            "tags": ["عميل_منتظم", "يفضل_المساء", "مهتم_بالجودة"]
        },
        {
            "customer_id": "CUST002",
            "phone": "+966509876543",
            "customer_name": "سارة عبدالله",
            "customer_email": "sara@example.com",
            "instagram_handle": "@sara_style",
            "total_orders": 2,
            "order_history": ["456", "450"],
            "preferences": ["تفضل التوصيل الصباحي"],
            "notes": ["عميلة جديدة"],
            "chat_summary": "عميلة جديدة تستفسر عن الطلبات",
            "last_interaction": int(time.time()),
            "satisfaction_score": 4.5,
            "tags": ["عميل_جديد", "تفضل_الصباح"]
        }
    ]
    for customer in customer_data:
        customer_collection.data.insert(customer)
    print("[SUCCESS] Customer files added!")

    # Add test messages
    print("\n3. Adding test messages...")
    messages = [
        {
            "content": "مرحباً، عندي مشكلة في الطلب رقم #123",
            "sender": "customer",
            "timestamp": int(time.time()),
            "sentiment": "neutral",
            "order_id": "123",
            "intent": "complaint",
            "customer_id": "CUST001"
        },
        {
            "content": "أهلاً بك! أنا هنا لمساعدتك. ما هي المشكلة بالضبط؟",
            "sender": "support",
            "timestamp": int(time.time()) + 60,
            "sentiment": "positive",
            "order_id": "123",
            "intent": "greeting",
            "customer_id": "CUST001"
        },
        {
            "content": "الطلب تأخر عن الموعد المحدد",
            "sender": "customer",
            "timestamp": int(time.time()) + 120,
            "sentiment": "negative",
            "order_id": "123",
            "intent": "complaint",
            "customer_id": "CUST001"
        },
        {
            "content": "مرحباً، أريد الاستفسار عن طلبي",
            "sender": "customer",
            "timestamp": int(time.time()) + 180,
            "sentiment": "neutral",
            "order_id": "456",
            "intent": "inquiry",
            "customer_id": "CUST002"
        }
    ]
    for message in messages:
        messages_collection.data.insert(message)
    print("[SUCCESS] Test messages added!")

    # Search for similar messages
    print("\n4. Testing message search...")
    message_results = messages_collection.query.bm25(
        query="مشكلة في الطلب",
        limit=2
    )

    print("\nMessage search results:")
    for obj in message_results.objects:
        print(f"- محتوى: {obj.properties['content']}".encode('utf-8').decode('utf-8'))
        print(f"  * المرسل: {obj.properties['sender']}".encode('utf-8').decode('utf-8'))
        print(f"  * رقم الطلب: {obj.properties['order_id']}".encode('utf-8').decode('utf-8'))
        print(f"  * المشاعر: {obj.properties['sentiment']}".encode('utf-8').decode('utf-8'))
        print(f"  * القصد: {obj.properties['intent']}".encode('utf-8').decode('utf-8'))
        print()

    # Search for customer file by phone
    print("\n5. Testing customer file search...")
    customer = customer_collection.query.fetch_objects(
        filters=weaviate.classes.query.Filter.by_property("phone").equal("+966501234567")
    )

    print("\nCustomer file:")
    if customer.objects:
        obj = customer.objects[0]
        print(f"- الاسم: {obj.properties['customer_name']}".encode('utf-8').decode('utf-8'))
        print(f"  * البريد الإلكتروني: {obj.properties['customer_email']}".encode('utf-8').decode('utf-8'))
        print(f"  * حساب انستغرام: {obj.properties['instagram_handle']}".encode('utf-8').decode('utf-8'))
        print(f"  * عدد الطلبات: {obj.properties['total_orders']}".encode('utf-8').decode('utf-8'))
        print(f"  * سجل الطلبات: {', '.join(obj.properties['order_history'])}".encode('utf-8').decode('utf-8'))
        print(f"  * التفضيلات: {', '.join(obj.properties['preferences'])}".encode('utf-8').decode('utf-8'))
        print(f"  * الملاحظات: {', '.join(obj.properties['notes'])}".encode('utf-8').decode('utf-8'))
        print(f"  * ملخص المحادثات: {obj.properties['chat_summary']}".encode('utf-8').decode('utf-8'))
        print(f"  * درجة الرضا: {obj.properties['satisfaction_score']}".encode('utf-8').decode('utf-8'))
        print(f"  * الوسوم: {', '.join(obj.properties['tags'])}".encode('utf-8').decode('utf-8'))
    else:
        print("[خطأ] لم يتم العثور على ملف العميل")


    # Get all messages
    print("\nAll messages:")
    all_messages = messages_collection.query.fetch_objects()
    for obj in all_messages.objects:
        print(f"- محتوى: {obj.properties['content']}".encode('utf-8').decode('utf-8'))
        print(f"  * المرسل: {obj.properties['sender']}".encode('utf-8').decode('utf-8'))
        print(f"  * رقم الطلب: {obj.properties['order_id']}".encode('utf-8').decode('utf-8'))
        print(f"  * المشاعر: {obj.properties['sentiment']}".encode('utf-8').decode('utf-8'))
        print(f"  * القصد: {obj.properties['intent']}".encode('utf-8').decode('utf-8'))
        print()


except Exception as e:
    print(f"[ERROR] {str(e)}")
finally:
    if 'client' in locals():
        client.close()
