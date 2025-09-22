import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('token_here')
    API_KEY = os. getenv('API_HERE')
    CAMP_URL = "URL_here"