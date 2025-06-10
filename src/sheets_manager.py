from typing import Dict, Any, Optional, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

class GoogleSheetsManager:
    def __init__(self, spreadsheet_id: str, credentials_dict: Dict[str, Any]):
        self.spreadsheet_id = spreadsheet_id
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheets = self.service.spreadsheets()

    async def search_knowledge_base(self, query: str) -> str:
        """Search the knowledge base for relevant information"""
        # Get all data from the Q&A sheet
        result = self.sheets.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='Q&A!A2:F'
        ).execute()
        
        values = result.get('values', [])
        relevant_info = []
        
        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()
        
        for row in values:
            if len(row) >= 6:  # Make sure we have ManualQuestion and ManualAnswer
                manual_q = row[4].lower() if len(row) > 4 and row[4] else ''
                manual_a = row[5] if len(row) > 5 and row[5] else ''
                
                # Check if query matches manual question
                if query_lower in manual_q:
                    relevant_info.append({
                        'question': row[4],
                        'answer': manual_a,
                        'relevance': 1.0 if query_lower == manual_q else 0.5
                    })
        
        # Sort by relevance
        relevant_info.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Format response
        if relevant_info:
            response = []
            for info in relevant_info[:3]:  # Only take top 3 matches
                response.append(f"س: {info['question']}\nج: {info['answer']}")
            return "\n\n".join(response)
        
        return "لم يتم العثور على معلومات ذات صلة في قاعدة البيانات. يرجى إعادة صياغة السؤال أو التوضيح أكثر."

    async def log_interaction(self, timestamp: str, contact_id: str, 
                            user_question: str, bot_answer: str):
        """Log the interaction in the Google Sheet"""
        try:
            values = [[timestamp, contact_id, user_question, bot_answer]]
            
            self.sheets.values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Q&A!A:D',  # First 4 columns: Timestamp, ContactID, UserQuestion, BotAnswer
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': values}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error logging interaction: {str(e)}")
            return False
