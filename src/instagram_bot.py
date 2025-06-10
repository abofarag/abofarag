from instabot import Bot
from typing import Optional, Dict, Any
import os
import time

class InstagramBot:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.bot = Bot()
        self._login()

    def _login(self):
        """Login to Instagram"""
        self.bot.login(username=self.username, password=self.password)

    def send_dm(self, user_id: str, message: str) -> bool:
        """Send a direct message to a user"""
        return self.bot.send_message(message, user_id)

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get information about a user"""
        user_id = self.bot.get_user_id_from_username(username)
        if user_id:
            return self.bot.get_user_info(user_id)
        return None

    def follow_user(self, username: str) -> bool:
        """Follow a user"""
        user_id = self.bot.get_user_id_from_username(username)
        if user_id:
            return self.bot.follow(user_id)
        return False
