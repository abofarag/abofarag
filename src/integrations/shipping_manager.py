import os
from typing import Dict, Optional
from datetime import datetime
import requests

class ShippingManager:
    def __init__(self):
        self.rgs_api_key = os.getenv('RGS_API_KEY')
        self.aramex_api_key = os.getenv('ARAMEX_API_KEY')
        self.aymakan_api_key = os.getenv('AYMAKAN_API_KEY')
    
    async def track_shipment(self, tracking_number: str, company: str) -> Dict:
        """تتبع الشحنة باستخدام رقم التتبع وشركة الشحن"""
        if company.lower() == 'rgs':
            return await self._track_rgs(tracking_number)
        elif company.lower() == 'aramex':
            return await self._track_aramex(tracking_number)
        elif company.lower() == 'aymakan':
            return await self._track_aymakan(tracking_number)
        else:
            return {
                'status': 'error',
                'message': f'شركة الشحن {company} غير مدعومة'
            }
    
    async def _track_rgs(self, tracking_number: str) -> Dict:
        """تتبع شحنة RGS"""
        try:
            headers = {
                'Authorization': f'Bearer {self.rgs_api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://api.rgs.com/v1/tracking/{tracking_number}',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'company': 'RGS',
                    'tracking_number': tracking_number,
                    'current_status': data.get('status'),
                    'location': data.get('current_location'),
                    'estimated_delivery': data.get('estimated_delivery'),
                    'last_update': data.get('last_update'),
                    'history': data.get('tracking_history', [])
                }
            else:
                return {
                    'status': 'error',
                    'message': 'فشل في تتبع الشحنة'
                }
        except Exception as e:
            print(f"Error tracking RGS shipment: {e}")
            return {
                'status': 'error',
                'message': 'حدث خطأ في تتبع الشحنة'
            }
    
    async def _track_aramex(self, tracking_number: str) -> Dict:
        """تتبع شحنة Aramex"""
        try:
            headers = {
                'Authorization': f'Bearer {self.aramex_api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://api.aramex.com/v1/tracking/shipments/{tracking_number}',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'company': 'Aramex',
                    'tracking_number': tracking_number,
                    'current_status': data.get('status'),
                    'location': data.get('current_location'),
                    'estimated_delivery': data.get('estimated_delivery'),
                    'last_update': data.get('last_update'),
                    'history': data.get('tracking_history', [])
                }
            else:
                return {
                    'status': 'error',
                    'message': 'فشل في تتبع الشحنة'
                }
        except Exception as e:
            print(f"Error tracking Aramex shipment: {e}")
            return {
                'status': 'error',
                'message': 'حدث خطأ في تتبع الشحنة'
            }
    
    async def _track_aymakan(self, tracking_number: str) -> Dict:
        """تتبع شحنة AyMakan"""
        try:
            headers = {
                'Authorization': f'Bearer {self.aymakan_api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://api.aymakan.com.sa/v2/tracking/{tracking_number}',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'company': 'AyMakan',
                    'tracking_number': tracking_number,
                    'current_status': data.get('status'),
                    'location': data.get('current_location'),
                    'estimated_delivery': data.get('estimated_delivery'),
                    'last_update': data.get('last_update'),
                    'history': data.get('tracking_history', [])
                }
            else:
                return {
                    'status': 'error',
                    'message': 'فشل في تتبع الشحنة'
                }
        except Exception as e:
            print(f"Error tracking AyMakan shipment: {e}")
            return {
                'status': 'error',
                'message': 'حدث خطأ في تتبع الشحنة'
            }
