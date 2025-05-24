from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Message(BaseModel):
    content: str
    timestamp: datetime
    is_from_customer: bool
    
class Order(BaseModel):
    order_id: str
    customer_id: str
    products: List[dict]
    total_amount: float
    shipping_address: dict
    status: str
    tracking_number: Optional[str]
    created_at: datetime
    
class Customer(BaseModel):
    customer_id: str
    instagram_id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    chat_history: List[Message]
    orders: List[Order]
    created_at: datetime
    last_interaction: datetime
