import os
from typing import Dict, List, Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsManager:
    def __init__(self):
        self.credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        self.orders_sheet_id = os.getenv('ORDERS_SHEET_ID')
        self.customers_sheet_id = os.getenv('CUSTOMERS_SHEET_ID')
        self.service = self._create_service()
        
    def _create_service(self):
        """إنشاء اتصال بخدمة Google Sheets"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            return build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            print(f"Error creating Google Sheets service: {e}")
            return None
    
    def add_order(self, order_data: Dict) -> bool:
        """إضافة طلب جديد إلى جدول الطلبات"""
        try:
            # تنسيق بيانات الطلب
            row = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # تاريخ الطلب
                order_data.get('order_id', ''),                # رقم الطلب
                order_data.get('customer_name', ''),           # اسم العميل
                order_data.get('customer_phone', ''),          # رقم الهاتف
                order_data.get('products', ''),                # المنتجات
                order_data.get('total_amount', ''),            # المبلغ الإجمالي
                order_data.get('shipping_address', ''),        # عنوان الشحن
                order_data.get('shipping_company', ''),        # شركة الشحن
                order_data.get('tracking_number', ''),         # رقم التتبع
                'جديد'                                        # حالة الطلب
            ]
            
            # إضافة الصف إلى الجدول
            self.service.spreadsheets().values().append(
                spreadsheetId=self.orders_sheet_id,
                range='Orders!A:J',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row]}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error adding order to sheet: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """تحديث حالة الطلب"""
        try:
            # البحث عن الطلب
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.orders_sheet_id,
                range='Orders!A:B'
            ).execute()
            
            rows = result.get('values', [])
            row_number = None
            
            for i, row in enumerate(rows):
                if len(row) > 1 and row[1] == order_id:
                    row_number = i + 1
                    break
            
            if row_number:
                # تحديث حالة الطلب
                range_name = f'Orders!J{row_number}'
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.orders_sheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[status]]}
                ).execute()
                return True
                
            return False
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    def get_customer_history(self, phone: str) -> List[Dict]:
        """استرجاع سجل طلبات العميل"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.orders_sheet_id,
                range='Orders!A:J'
            ).execute()
            
            rows = result.get('values', [])
            customer_orders = []
            
            for row in rows[1:]:  # تخطي الصف الأول (العناوين)
                if len(row) > 3 and row[3] == phone:
                    customer_orders.append({
                        'date': row[0],
                        'order_id': row[1],
                        'products': row[4],
                        'total_amount': row[5],
                        'status': row[9]
                    })
            
            return customer_orders
        except Exception as e:
            print(f"Error getting customer history: {e}")
            return []
    
    def search_order(self, query: str) -> Optional[Dict]:
        """البحث عن طلب باستخدام رقم الطلب أو رقم التتبع"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.orders_sheet_id,
                range='Orders!A:J'
            ).execute()
            
            rows = result.get('values', [])
            
            for row in rows[1:]:  # تخطي الصف الأول (العناوين)
                # البحث في رقم الطلب ورقم التتبع
                if (len(row) > 8 and 
                    (row[1] == query or  # رقم الطلب
                     row[8] == query)):  # رقم التتبع
                    return {
                        'date': row[0],
                        'order_id': row[1],
                        'customer_name': row[2],
                        'customer_phone': row[3],
                        'products': row[4],
                        'total_amount': row[5],
                        'shipping_address': row[6],
                        'shipping_company': row[7],
                        'tracking_number': row[8],
                        'status': row[9]
                    }
            
            return None
        except Exception as e:
            print(f"Error searching for order: {e}")
            return None
