# app/main.py
import logging
import sys
import os
import json
from database.mysql_db import MySQLTextDB
from gigachat.api_client import GigaChatClient
from processing.data_parser import DataParser
from bot.telegram_bot import TelegramBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cosmos_bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config(config_path="config.json"):
    """
    Загружает конфигурацию из JSON файла
    
    Args:
        config_path (str): Путь к файлу конфигурации
    
    Returns:
        dict: Словарь с конфигурацией
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"✅ Конфигурация загружена из {config_path}")
        return config
        
    except FileNotFoundError:
        logger.error(f"❌ Файл конфигурации {config_path} не найден")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON в файле {config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при загрузке конфигурации: {e}")
        raise

def validate_config(config):
    """
    Проверяет обязательные поля в конфигурации
    
    Args:
        config (dict): Загруженная конфигурация
    
    Returns:
        bool: True если конфигурация валидна
    """
    required_fields = [
        'telegram_bot_token',
        'gigachat_api_key',
        'mysql_config',
        'camp_url'
    ]
    
    for field in required_fields:
        if field not in config:
            logger.error(f"❌ Отсутствует обязательное поле: {field}")
            return False
    
    # Проверяем MySQL конфигурацию
    mysql_required = ['host', 'user', 'password', 'database']
    for field in mysql_required:
        if field not in config['mysql_config']:
            logger.error(f"❌ Отсутствует поле mysql_config.{field}")
            return False
    
    # Проверяем токены
    if not config['telegram_bot_token']:
        logger.error("❌ TELEGRAM_BOT_TOKEN не может быть пустым")
        return False
        
    if not config['gigachat_api_key']:
        logger.error("❌ GIGACHAT_API_KEY не может быть пустым")
        return False
    
    logger.info("✅ Конфигурация прошла валидацию")
    return True

def setup_database(database, camp_url):
    """
    Настраивает базу данных и загружает информацию
    
    Args:
        database: Экземпляр базы данных
        camp_url (str): URL лагеря для парсинга
    """
    try:
        count = database.get_document_count()
        if count > 0:
            logger.info(f"В базе уже есть {count} документов, пропускаем загрузку")
            return

        logger.info("Начинаем загрузку данных в базу...")

        parser = DataParser(camp_url)
        website_data = parser.parse_website()
        faq_data = parser.create_sample_faq()
        all_data = website_data + faq_data

        if not all_data:
            logger.warning("Не удалось получить данные для базы")
            return

        database.store_documents(all_data)
        logger.info(f"Успешно загружено {len(all_data)} документов в базу")

    except Exception as e:
        logger.error(f"Ошибка настройки базы данных: {e}")

def update_bot_contacts(bot, config):
    """
    Обновляет контактные данные в боте
    
    Args:
        bot: Экземпляр бота
        config (dict): Конфигурация
    """
    if 'contacts' in config:
        if 'phone' in config['contacts']:
            bot.contact_phone = config['contacts']['phone']
        if 'email' in config['contacts']:
            bot.contact_email = config['contacts']['email']
    
    bot.camp_website = config['camp_url']

def main():
    """Основная функция приложения"""
    try:
        logger.info("Запуск приложения лагеря 'Космос'...")
        
        # Загружаем конфигурацию
        config = load_config("config.json")
        
        # Проверяем конфигурацию
        if not validate_config(config):
            logger.error("❌ Невалидная конфигурация. Завершение работы.")
            return
        
        # Инициализация клиентов
        gigachat_client = GigaChatClient(config['gigachat_api_key'])
        database = MySQLTextDB(config['mysql_config'])

        # Настройка базы данных
        setup_database(database, config['camp_url'])

        # Проверяем что данные загружены
        count = database.get_document_count()
        if count == 0:
            logger.error("В базе нет данных! Бот не может работать без базы знаний.")
            return

        logger.info(f"База данных готова, документов: {count}")

        # Создаем и настраиваем бота
        bot = TelegramBot(
            config['telegram_bot_token'], 
            gigachat_client, 
            database
        )
        
        # Обновляем контактные данные
        update_bot_contacts(bot, config)
        
        # Запускаем бота
        logger.info("🤖 Запуск Telegram бота...")
        bot.run()

    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Закрываем соединения
        if 'database' in locals():
            database.close()
            logger.info("🔌 Соединение с базой данных закрыто")

if __name__ == "__main__":
    main()