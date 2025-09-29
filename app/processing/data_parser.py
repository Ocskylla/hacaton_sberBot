# app/processing/data_parser.py
import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)


class DataParser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

    def parse_legal_documents(self):
        """Парсинг юридических документов с pravo.gov.ru"""
        legal_documents = []
        
        # Список законов для парсинга (из изображения)
        laws_to_parse = [
            {
                'name': 'Федеральный закон №124-ФЗ «Об основных гарантиях прав ребёнка»',
                'article': 'ст. 12 ч. 2',
                'url': 'http://pravo.gov.ru/proxy/ips/?docbody=&nd=102058299'
            },
            {
                'name': 'Федеральный закон №273-ФЗ «Об образовании в Российской Федерации»',
                'article': 'ст. 28 ч. 7',
                'url': 'http://pravo.gov.ru/proxy/ips/?docbody=&nd=102162277'
            },
            {
                'name': 'Закон РФ №2300-1 «О защите прав потребителей»',
                'article': 'ст. 7 п. 1',
                'url': 'http://pravo.gov.ru/proxy/ips/?docbody=&nd=102030634'
            },
            {
                'name': 'Гражданский кодекс РФ',
                'article': 'ст. 1068',
                'url': 'http://pravo.gov.ru/proxy/ips/?docbody=&nd=102450098'
            },
            {
                'name': 'Гражданский кодекс РФ',
                'article': 'ст. 1095',
                'url': 'http://pravo.gov.ru/proxy/ips/?docbody=&nd=102450098'
            },
            {
                'name': 'Уголовный кодекс РФ',
                'article': 'ст. 293',
                'url': 'http://pravo.gov.ru/proxy/ips/?docbody=&nd=102450099'
            }
        ]

        for law in laws_to_parse:
            try:
                logger.info(f"Парсим закон: {law['name']} {law['article']}")
                
                response = self.session.get(law['url'], timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Удаляем скрипты и стили
                for element in soup(["script", "style", "nav", "header", "footer"]):
                    element.decompose()

                # Извлекаем основной контент
                main_text = self.extract_main_content(soup)
                cleaned_text = self.clean_text(main_text)

                if cleaned_text and len(cleaned_text) > 50:
                    # Создаем структурированное описание закона
                    law_content = f"""
{law['name']} {law['article']}

ОПИСАНИЕ:
Данный нормативный правовой акт регулирует вопросы ответственности администрации детских лагерей за безопасность и жизнь детей.

ТЕКСТ ДОКУМЕНТА:
{cleaned_text[:3000]}

ОТВЕТСТВЕННОСТЬ ДЕТСКОГО ЛАГЕРЯ:
- Администрация лагеря несет ответственность за жизнь и здоровье детей
- Обязана обеспечивать безопасные условия пребывания
- Отвечает за действия сотрудников
- Несет гражданско-правовую ответственность за причиненный вред
"""

                    legal_documents.append({
                        'source': law['url'],
                        'content': law_content,
                        'type': 'legal_document',
                        'chunk_index': 0,
                        'law_name': law['name'],
                        'article': law['article']
                    })
                    
                    logger.info(f"✅ Успешно распарсен закон: {law['name']} {law['article']}")

                time.sleep(2)  # Задержка между запросами

            except Exception as e:
                logger.warning(f"⚠️ Не удалось распарсить закон {law['name']}: {e}")
                continue

        # Добавляем обобщающий документ о правовой ответственности
        responsibility_summary = """
ОТВЕТСТВЕННОСТЬ АДМИНИСТРАЦИИ ДЕТСКИХ ЛАГЕРЕЙ ПО ЗАКОНОДАТЕЛЬСТВУ РФ

НОРМАТИВНЫЕ ПРАВОВЫЕ АКТЫ, РЕГУЛИРУЮЩИЕ ОТВЕТСТВЕННОСТЬ:

1. "Федеральный закон №124-ФЗ «Об основных гарантиях прав ребёнка»"
   - Статья 12 часть 2: Закрепляет обязанность лагеря обеспечивать безопасность и сохранение жизни и здоровья детей.

2. "Федеральный закон №273-ФЗ «Об образовании в Российской Федерации»"
   - Статья 28 часть 7: Устанавливает ответственность образовательной организации за жизнь и здоровье обучающихся.

3. "Закон РФ №2300-1 «О защите прав потребителей»"
   - Статья 7 пункт 1: Определяет право потребителя на безопасность услуги.

4. "Гражданский кодекс РФ"
   - Статья 1068: Лагерь несет ответственность за неисполнение сотрудниками обязанностей по присмотру за детьми.
   - Статья 1095: Лагерь отвечает за вред, причиненный здоровью ребенка из-за отсутствия надлежащего присмотра.

5. "Уголовный кодекс РФ"
   - Статья 293: Устанавливает уголовную ответственность за халатность должностных лиц.

ВИДЫ ОТВЕТСТВЕННОСТИ:
- Гражданско-правовая: Возмещение вреда, причиненного жизни и здоровью
- Административная: Нарушение правил организации отдыха детей
- Уголовная: Халатность, повлекшая тяжкие последствия

ПРАВА РОДИТЕЛЕЙ:
- Требовать возмещения вреда, причиненного ребенку
- Обращаться в надзорные органы при нарушениях
- Получать полную информацию об условиях пребывания
"""

        legal_documents.append({
            'source': 'legal_summary',
            'content': responsibility_summary,
            'type': 'legal_document',
            'chunk_index': 1
        })

        logger.info(f"📚 Всего распарсено юридических документов: {len(legal_documents)}")
        return legal_documents

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
                            'content': content[:5000],
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

        # Добавляем юридические документы
        legal_docs = self.parse_legal_documents()
        all_data.extend(legal_docs)

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
            },
            {
                'question': 'Какая ответственность администрации лагеря за безопасность детей?',
                'answer': 'Администрация лагеря несет полную ответственность за безопасность детей согласно законодательству РФ, включая Федеральный закон №124-ФЗ, Гражданский кодекс РФ и другие нормативные акты.',
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