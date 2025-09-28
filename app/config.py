# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('8410273120:AAFIfyX8A-24x_72gQMs9WjVSDHS8T4K-1g')#сюды токен
    GIGACHAT_API_KEY = os.getenv('MDE5OTg3ODYtMWY2MC03ZTM1LTk1YTctMGQyOGNkYjdlNjViOmFiZTFlZGMyLWZkOGYtNGYzMy04NjRmLTBjNzVlMmY1MDA5OA==')#сюды апишку
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'dima1806'),#сюды пароль от дбшки
        'database': os.getenv('MYSQL_DATABASE', 'test')#сюды имя дбшки
    }
    CAMP_URL = os.getenv('CAMP_URL', 'https://cosmos.68edu.ru')