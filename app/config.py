# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('')#сюды токен
    GIGACHAT_API_KEY = os.getenv('')#сюды апишку
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),#сюды пароль от дбшки
        'database': os.getenv('MYSQL_DATABASE', '')#сюды имя дбшки
    }
    CAMP_URL = os.getenv('CAMP_URL', 'https://cosmos.68edu.ru')