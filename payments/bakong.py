import requests
import hashlib
import hmac
import json
from datetime import datetime
from flask import current_app




class BakongPayment:
    def __init__(self):
        self.api_url = current_app.config['BAKONG_API_URL']
        self.merchant_id = current_app.config['BAKONG_MERCHANT_ID']
        self.api_key = current_app.config['BAKONG_API_KEY']
        # self.secret_key = current_app.config['BAKONG_SECRET_KEY']

    def generate_signature(self, data):
        """Generate HMAC signature for Bakong API"""
        message = json.dumps(data, separators=(',', ':'))
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def create_payment(self, amount, currency='USD', description='Payment', order_id=None):
        """Create a Bakong payments request"""
        endpoint = f"{self.api_url}/v1/payments/create"

        payload = {
            'merchant_id': self.merchant_id,
            'amount': float(amount),
            'currency': currency,
            'description': description,
            'order_id': order_id or self.generate_order_id(),
            'callback_url': current_app.config['PAYMENT_CALLBACK_URL'] + '/bakong',
            'timestamp': datetime.utcnow().isoformat()
        }

        signature = self.generate_signature(payload)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Signature': signature
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_qr_code(self, payment_id):
        """Generate QR code for Bakong payments"""
        endpoint = f"{self.api_url}/v1/payments/qr/{payment_id}"

        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            return {
                'success': True,
                'qr_code': response.json().get('qr_code')
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def verify_callback(self, callback_data, signature):
        """Verify callback signature from Bakong"""
        expected_signature = self.generate_signature(callback_data)
        return hmac.compare_digest(expected_signature, signature)

    def check_payment_status(self, payment_id):
        """Check payments status"""
        endpoint = f"{self.api_url}/v1/payments/status/{payment_id}"

        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def generate_order_id():
        """Generate unique order ID"""
        import uuid
        return f"BKG-{uuid.uuid4().hex[:12].upper()}"