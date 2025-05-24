from fastapi import APIRouter, HTTPException
from ..core.vector_store import VectorStore

router = APIRouter()

@router.get("/health")
async def health_check():
    """التحقق من صحة الخدمة والاتصال بـ Weaviate"""
    try:
        vector_store = VectorStore()
        # محاولة حفظ رسالة اختبار
        message_id = await vector_store.save_message(
            customer_id="test_health",
            content="رسالة اختبار الصحة",
            is_from_customer=True
        )
        
        return {
            "status": "healthy",
            "weaviate_connection": "connected",
            "test_message_id": message_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في الاتصال: {str(e)}"
        )
