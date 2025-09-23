# app/processing/data_parser.py
import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class DataParser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def clean_text(self, text):
        """Очистка текста от лишних пробелов и символов"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    def parse_website(self):
        """Парсинг основных страниц сайта лагеря"""
        pages_to_parse = [
            '/about', '/o-lagere', '/programs', '/programmy',
            '/parents', '/roditelyam', '/documents', '/dokumenty',
            '/safety', '/bezopasnost', '/contacts', '/kontakty'
        ]

        all_data = []

        for page in pages_to_parse:
            try:
                url = urljoin(self.base_url, page)
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Удаляем скрипты и стили
                for script in soup(["script", "style"]):
                    script.decompose()

                # Извлекаем заголовок и основной текст
                title = soup.find('title')
                title_text = title.get_text() if title else ""

                # Ищем основной контент
                main_content = soup.find('main') or soup.find('article') or soup.find('div',
                                                                                      class_=re.compile('content|main'))
                if main_content:
                    text = main_content.get_text()
                else:
                    text = soup.get_text()

                cleaned_text = self.clean_text(text)

                if cleaned_text and len(cleaned_text) > 100:  # Минимальная длина текста
                    all_data.append({
                        'source': url,
                        'content': f"{title_text}\n\n{cleaned_text}"[:5000],  # Ограничиваем длину
                        'type': 'website'
                    })
                    logger.info(f"Успешно распарсена страница: {url}")

            except Exception as e:
                logger.warning(f"Не удалось распарсить страницу {page}: {e}")
                continue

        # Если не нашли страниц, пробуем парсить главную страницу
        if not all_data:
            try:
                response = self.session.get(self.base_url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()
                cleaned_text = self.clean_text(text)

                if cleaned_text:
                    all_data.append({
                        'source': self.base_url,
                        'content': cleaned_text[:5000],
                        'type': 'website'
                    })
            except Exception as e:
                logger.error(f"Не удалось распарсить главную страницу: {e}")

        return all_data

    def create_sample_faq(self):
        """Создание примерного FAQ, если нет реальных данных"""
        sample_faq = [
            {
                'question': 'Какие документы нужны для заезда в лагерь?',
                'answer': 'Для заезда в лагерь необходимы: паспорт родителя, свидетельство о рождении ребенка, медицинская справка формы 079/у, справка об отсутствии контактов с инфекционными больными, копия медицинского полиса.',
                'type': 'faq'
            },
            {
                'question': 'Какова стоимость путевки?',
                'answer': 'Стоимость путевки зависит от сезона и программы смены. Актуальные цены уточняйте у администрации лагеря по телефону.',
                'type': 'faq'
            },
            {
                'question': 'Какие меры безопасности предусмотрены в лагере?',
                'answer': 'Лагерь обеспечен круглосуточной охраной, видеонаблюдением, медицинским пунктом. Все вожатые проходят специальную подготовку по безопасности детей.',
                'type': 'faq'
            }
        ]

        # Конвертируем FAQ в формат документов
        documents = []
        for i, item in enumerate(sample_faq):
            content = f"Вопрос: {item['question']}\nОтвет: {item['answer']}"
            documents.append({
                'source': 'sample_faq',
                'content': content,
                'type': 'faq'
            })

        return documents