from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        
    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            
    @classmethod
    def get_db(cls):
        return cls.client[settings.DB_NAME]
        
    @classmethod
    async def get_customer_history(cls, customer_id: str):
        """Retrieve customer's chat history and order history"""
        db = cls.get_db()
        customer = await db.customers.find_one({"customer_id": customer_id})
        return customer
        
    @classmethod
    async def save_chat_message(cls, customer_id: str, message: dict):
        """Save chat message to database"""
        db = cls.get_db()
        await db.chat_history.insert_one({
            "customer_id": customer_id,
            "message": message,
            "timestamp": message.get("timestamp")
        })
        
    @classmethod
    async def save_order(cls, order_data: dict):
        """Save order information to database"""
        db = cls.get_db()
        await db.orders.insert_one(order_data)
