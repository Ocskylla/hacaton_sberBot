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
        """Очистка текста от лишних пробелов и переносов"""
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def extract_main_content(self, soup):
        """Извлечение основного контента страницы"""
        # Попробуем найти основной контент разными способами
        selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.page-content',
            '#content',
            '#main',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text()
        
        # Если не нашли специфичный контейнер, берем body
        return soup.find('body').get_text() if soup.find('body') else soup.get_text()

    def parse_website(self):
        """Парсинг веб-сайта лагеря"""
        pages_to_parse = [
            '/czto-kosmos', '/osnovnye-svedeniya', '/deyatelnost',
            '/fotogalereya/infrastruktura', '/profilnye-smeny', '/roditelyam',
            '/dostupnaya-sreda', '/oplata', '/struktura_i_organy',
            '/nashi-dostizheniya', '/muzej-czto-kosmos', '/fotogalereya/usloviya-prozhivaniya',
            '/dokumenty', '/kontakty'
        ]

        all_data = []

        for page in pages_to_parse:
            try:
                url = urljoin(self.base_url, page)
                logger.info(f"Парсим страницу: {url}")
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Удаляем скрипты и стили
                for element in soup(["script", "style", "nav", "header", "footer"]):
                    element.decompose()

                # Извлекаем заголовок
                title = soup.find('title')
                title_text = self.clean_text(title.get_text()) if title else ""

                # Извлекаем основной контент
                main_text = self.extract_main_content(soup)
                cleaned_text = self.clean_text(main_text)

                # Проверяем, что текст достаточно содержательный
                if cleaned_text and len(cleaned_text) > 50:
                    content = f"{title_text}\n\n{cleaned_text}"
                    
                    # Разбиваем на чанки если текст слишком большой
                    if len(content) > 4000:
                        chunks = self.split_text(content, max_length=4000)
                        for i, chunk in enumerate(chunks):
                            all_data.append({
                                'source': url,
                                'content': chunk,
                                'type': 'website',
                                'chunk_index': i
                            })
                    else:
                        all_data.append({
                            'source': url,
                            'content': content[:5000],  # Ограничиваем длину
                            'type': 'website',
                            'chunk_index': 0
                        })
                    
                    logger.info(f"✅ Успешно распарсена страница: {url} (символов: {len(cleaned_text)})")

            except Exception as e:
                logger.warning(f"⚠️ Не удалось распарсить страницу {page}: {e}")
                continue

        # Если не получилось распарсить отдельные страницы, пробуем главную
        if not all_data:
            try:
                logger.info("Пробуем распарсить главную страницу...")
                response = self.session.get(self.base_url, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for element in soup(["script", "style", "nav", "header", "footer"]):
                    element.decompose()
                
                title = soup.find('title')
                title_text = self.clean_text(title.get_text()) if title else ""
                main_text = self.extract_main_content(soup)
                cleaned_text = self.clean_text(main_text)
                
                if cleaned_text:
                    all_data.append({
                        'source': self.base_url,
                        'content': f"{title_text}\n\n{cleaned_text}"[:5000],
                        'type': 'website',
                        'chunk_index': 0
                    })
                    logger.info(f"✅ Распарсена главная страница")
            except Exception as e:
                logger.error(f"❌ Не удалось распарсить главную страницу: {e}")

        logger.info(f"📊 Всего распарсено документов: {len(all_data)}")
        return all_data

    def split_text(self, text, max_length=4000):
        """Разбивает текст на чанки по предложениям"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def create_sample_faq(self):
        """Создание образцов FAQ"""
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
            },
            {
                'question': 'Какие возрастные группы принимаются в лагерь?',
                'answer': 'Лагерь принимает детей в возрасте от 7 до 17 лет. Группы формируются по возрастным категориям.',
                'type': 'faq'
            },
            {
                'question': 'Есть ли в лагере Wi-Fi?',
                'answer': 'На территории лагеря есть ограниченный доступ к Wi-Fi для детей в специально отведенное время.',
                'type': 'faq'
            }
        ]

        documents = []
        for i, item in enumerate(sample_faq):
            content = f"Вопрос: {item['question']}\nОтвет: {item['answer']}"
            documents.append({
                'source': 'sample_faq',
                'content': content,
                'type': 'faq',
                'chunk_index': i
            })

        logger.info(f"📋 Создано FAQ документов: {len(documents)}")
        return documents