# app/main.py
import logging
import sys
import os
from app.config import Config
from app.database.mysql_db import MySQLVectorDB
from app.gigachat.api_client import GigaChatClient
from app.processing.data_parser import DataParser
from app.bot.telegram_bot import TelegramBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cosmos_bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_database(gigachat_client, database):
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


        texts = [doc['content'] for doc in all_data]
        embeddings = gigachat_client.get_embeddings(texts)

        if embeddings:
            for i, doc in enumerate(all_data):
                doc['embedding'] = embeddings[i]
        else:
            logger.warning("Не удалось получить эмбеддинги, сохраняем документы без них")


        database.store_documents(all_data)
        logger.info(f"Успешно загружено {len(all_data)} документов в базу")

    except Exception as e:
        logger.error(f"Ошибка настройки базы данных: {e}")


def main():
    try:
        logger.info("Запуск приложения лагеря 'Космос'...")


        config = Config()
        gigachat_client = GigaChatClient(config.GIGACHAT_API_KEY)
        database = MySQLVectorDB(config.MYSQL_CONFIG)


        setup_database(gigachat_client, database)


        count = database.get_document_count()
        if count == 0:
            logger.error("В базе нет данных! Бот не может работать без базы знаний.")
            return

        logger.info(f"База данных готова, документов: {count}")


        bot = TelegramBot(config.TELEGRAM_BOT_TOKEN, gigachat_client, database)
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