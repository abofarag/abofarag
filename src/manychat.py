import requests
from typing import Dict, Any
from pydantic import BaseModel

class ManyChatAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.manychat.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def send_message(self, subscriber_id: str, message: str) -> Dict[str, Any]:
        """Send a text message to a ManyChat subscriber."""
        endpoint = f"{self.base_url}/fb/sending/sendContent"
        payload = {
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
        response = requests.post(endpoint, headers=self.headers, json=payload)
        return response.json()
