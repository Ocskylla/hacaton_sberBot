# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('')#токен сюды
    GIGACHAT_API_KEY = os.getenv('')#апишку сюды
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'Ocskylla1337'),
        'database': os.getenv('MYSQL_DATABASE', 'MYSQL')
    }
    CAMP_URL = os.getenv('CAMP_URL', 'https://cosmos.68edu.ru')