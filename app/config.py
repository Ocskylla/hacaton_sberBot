# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('')
    GIGACHAT_API_KEY = os.getenv('')
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'cosmos_camp_db')
    }
    CAMP_URL = os.getenv('CAMP_URL', 'https://camp-cosmos.ru')# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    GIGACHAT_API_KEY = os.getenv('GIGACHAT_API_KEY')
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'cosmos_camp_db')
    }

    CAMP_URL = os.getenv('CAMP_URL', 'https://camp-cosmos.ru')
