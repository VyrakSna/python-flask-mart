import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    # Bakong Configuration
    BAKONG_API_URL = "https://api-bakong.nbc.gov.kh"  # Production URL
    BAKONG_MERCHANT_ID = os.getenv('BAKONG_MERCHANT_ID')
    BAKONG_API_KEY = os.getenv('BAKONG_API_KEY')
    BAKONG_SECRET_KEY = os.getenv('BAKONG_SECRET_KEY')

    # ABA PayWay Configuration
    ABA_API_URL = "https://checkout.payway.com.kh/api"  # Production URL
    ABA_MERCHANT_ID = os.getenv('ABA_MERCHANT_ID')
    ABA_API_KEY = os.getenv('ABA_API_KEY')
    ABA_API_SECRET = os.getenv('ABA_API_SECRET')

    # General Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    PAYMENT_CALLBACK_URL = os.getenv('PAYMENT_CALLBACK_URL', 'http://localhost:5000/payment/callback')