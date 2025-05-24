import weaviate
from typing import Dict, List, Optional
from datetime import datetime
from ..core.config import settings

class VectorStore:
    def __init__(self):
        self._client = None
        self._connect()
        self._create_schema()
        
    def _connect(self):
        """Establish connection to Weaviate"""
        if self._client is None:
            self._client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY),
            )
        
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        if hasattr(self, '_client') and self._client is not None:
            self._client.close()
            self._client = None

    def _create_schema(self):
        """Create schema for customer conversations"""
        try:
            self._connect()
            schema = {
                "class": "CustomerMessage",
                "vectorizer": "text2vec-contextionary",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The message content",
                    },
                    {
                        "name": "customer_id",
                        "dataType": ["string"],
                        "description": "Customer identifier",
                    },
                    {
                        "name": "timestamp",
                        "dataType": ["date"],
                        "description": "When the message was sent",
                    },
                    {
                        "name": "message_type",
                        "dataType": ["string"],
                        "description": "Type of message (text, image, voice)",
                    },
                    {
                        "name": "is_from_customer",
                        "dataType": ["boolean"],
                        "description": "Whether message is from customer",
                    },
                    {
                        "name": "media_url",
                        "dataType": ["string"],
                        "description": "URL for media content if any",
                    }
                ],
            }
            
            try:
                self._client.schema.create_class(schema)
            except weaviate.exceptions.UnexpectedStatusCodeException:
                # Schema might already exist
                pass
        finally:
            if self._client:
                self._client.close()

    async def save_message(self, 
                          customer_id: str, 
                          content: str, 
                          is_from_customer: bool,
                          message_type: str = "text",
                          media_url: Optional[str] = None) -> str:
        """Save a message to the vector store"""
        try:
            self._connect()
            properties = {
                "content": content,
                "customer_id": customer_id,
                "timestamp": datetime.now().isoformat(),
                "message_type": message_type,
                "is_from_customer": is_from_customer,
                "media_url": media_url
            }
            
            result = self._client.data_object.create(
                "CustomerMessage",
                properties
            )
            return result.uuid
        finally:
            if self._client:
                self._client.close()

    async def get_conversation_context(self, 
                                     customer_id: str, 
                                     limit: int = 10) -> List[Dict]:
        """Get recent conversation context for a customer"""
        try:
            self._connect()
            query = (
                self._client.query
                .get("CustomerMessage", ["content", "timestamp", "message_type", "is_from_customer", "media_url"])
                .with_where({
                    "path": ["customer_id"],
                    "operator": "Equal",
                    "valueString": customer_id
                })
                .with_sort({"path": ["timestamp"], "order": "desc"})
                .with_limit(limit)
            )
            
            result = query.do()
            messages = result.get('data', {}).get('Get', {}).get('CustomerMessage', [])
            return messages
        finally:
            if self._client:
                self._client.close()

    async def search_similar_conversations(self, 
                                        query: str, 
                                        limit: int = 5) -> List[Dict]:
        """Search for similar conversations using semantic search"""
        try:
            self._connect()
            result = (
                self._client.query
                .get("CustomerMessage", ["content", "customer_id", "timestamp"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            return result.get('data', {}).get('Get', {}).get('CustomerMessage', [])
        finally:
            if self._client:
                self._client.close()
