# app/main.py
import logging
import sys
import os
from config import Config
from database.mysql_db import MySQLTextDB  # Изменен импорт
from gigachat.api_client import GigaChatClient
from processing.data_parser import DataParser
from bot.telegram_bot import TelegramBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cosmos_bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_database(database):  # Убран gigachat_client
    try:
        count = database.get_document_count()
        if count > 0:
            logger.info(f"В базе уже есть {count} документов, пропускаем загрузку")
            return

        logger.info("Начинаем загрузку данных в базу...")

        parser = DataParser(Config.CAMP_URL)
        website_data = parser.parse_website()
        faq_data = parser.create_sample_faq()
        all_data = website_data + faq_data

        if not all_data:
            logger.warning("Не удалось получить данные для базы")
            return

        # Сохраняем документы без эмбеддингов
        database.store_documents(all_data)
        logger.info(f"Успешно загружено {len(all_data)} документов в базу")

    except Exception as e:
        logger.error(f"Ошибка настройки базы данных: {e}")

def main():
    try:
        logger.info("Запуск приложения лагеря 'Космос'...")

        config = Config()
        gigachat_client = GigaChatClient('MDE5OTg3ODYtMWY2MC03ZTM1LTk1YTctMGQyOGNkYjdlNjViOmFiZTFlZGMyLWZkOGYtNGYzMy04NjRmLTBjNzVlMmY1MDA5OA==')
        database = MySQLTextDB(config.MYSQL_CONFIG)  # Используем новую класс

        setup_database(database)  # Убран gigachat_client

        count = database.get_document_count()
        if count == 0:
            logger.error("В базе нет данных! Бот не может работать без базы знаний.")
            return

        logger.info(f"База данных готова, документов: {count}")

        bot = TelegramBot('8410273120:AAFIfyX8A-24x_72gQMs9WjVSDHS8T4K-1g', gigachat_client, database)
        bot.run()

    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        if 'database' in locals():
            database.close()

if __name__ == "__main__":
    main()