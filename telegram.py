from http.client import responses

import requests
import time
token =  '7808540343:AAEq_c473X_U3BSM-ofTyFKLmgwS6G3GOvs'
def sendMessage(chat_id: str, message: str ):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }
    response = requests.post(url, json=payload)
