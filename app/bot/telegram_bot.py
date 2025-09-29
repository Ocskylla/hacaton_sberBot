# app/bot/telegram_bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import re

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, gigachat_client, database):
        self.token = token
        self.gigachat = gigachat_client
        self.db = database
        self.application = None
        self.contact_phone = "+7 (4752) 55-70-09"  
        self.camp_website = "https://cosmos.68edu.ru"

    def _format_response(self, response):
        """Форматирует ответ согласно правилам"""
        
        # Правило 3: Форматирование перечислений
        response = re.sub(r'(\d+)\.\s*"([^"]+)"\.\s*', r'\1. "\2". ', response)
        
        # Правило 1: Обработка ссылок
        response = re.sub(r'([\w\s]+):\s*(https?://[^\s]+)', r'\1: \2', response)
        
        # Правило 2: Обработка email
        response = re.sub(r'["\']([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', r'\1', response)
        
        # Правило 4: Обращения "Вам", "Вы" с заглавной буквы
        response = re.sub(r'\bвам\b', 'Вам', response)
        response = re.sub(r'\bвы\b', 'Вы', response)
        response = re.sub(r'\bВаш\b', 'Ваш', response)
        response = re.sub(r'\bваш\b', 'Ваш', response)
        
        # Дополнительное форматирование для улучшения читаемости
        sentences = response.split('. ')
        formatted_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                if not sentence.endswith('.'):
                    sentence += '.'
                formatted_sentences.append(sentence.strip())
        
        response = ' '.join(formatted_sentences)
        
        return response

    def _should_add_phone_contact(self, question, response):
        """Определяет, нужно ли добавлять контактный телефон"""
        contact_keywords = [
            'связь', 'связаться', 'контакт', 'телефон', 'позвонить', 'звонок',
            'администрация', 'руководство', 'директор', 'начальник',
            'ребенок', 'дети', 'сын', 'дочь', 'позвонить ребенку',
            'связь с ребенком', 'связаться с детьми', 'общение с детьми',
            'родительский день', 'посещение', 'встреча'
        ]
        
        question_lower = question.lower()
        response_lower = response.lower()
        
        # Проверяем, есть ли ключевые слова в вопросе
        has_contact_keywords = any(keyword in question_lower for keyword in contact_keywords)
        
        # Проверяем, упоминается ли администрация в ответе
        has_administration_mention = any(word in response_lower for word in ['администрац', 'руководств', 'директор'])
        
        return has_contact_keywords or has_administration_mention

    def _should_redirect_to_website(self, question):
        """Определяет, относится ли вопрос к стоимости"""
        price_keywords = [
            'стоимость', 'цена', 'сколько стоит', 'ценник', 'прайс',
            'оплата', 'платить', 'деньги', 'бюджет', 'путевка',
            'расходы', 'затраты', 'тариф', 'стоит'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in price_keywords)

    def _create_formatted_prompt(self, context, question):
        """Создает промпт с инструкциями по форматированию"""
        
        formatting_rules = """
ПРИ ФОРМИРОВАНИИ ОТВЕТА СОБЛЮДАЙТЕ СЛЕДУЮЩИЕ ПРАВИЛА ФОРМАТИРОВАНИЯ:

1. ССЫЛКИ: сайт пишется через пробел после двоеточия, следующего за непосредственным упоминанием ресурса.
   Пример: Наш сайт: https://cosmos.68edu.ru

2. EMAIL: адреса электронных почт указываются без кавычек.
   Пример: Пишите нам на email: kosmos@OBRAZ.TAMBOV.GOV.RU

3. ПЕРЕЧИСЛЕНИЯ: каждый пункт пишется с нового абзаца в формате:
   1. "Заголовок пункта". Текст пункта начинается с нового предложения.
   2. "Второй пункт". Описание второго пункта.

4. ОБРАЩЕНИЯ: обращения "Вам", "Вы", "Ваш" всегда пишутся с заглавной буквы.
   Пример: Для Вас необходимо предоставить следующие документы. Ваш ребенок будет находиться под присмотром.

5. КОНТАКТНЫЙ ТЕЛЕФОН: при вопросах о связи с представителями лагеря, контакте с детьми или упоминании администрации обязательно указывайте контактный телефон в круглых скобках.
   Пример: Для связи с администрацией лагеря (тел. +7 (4752) 55-70-09) Вы можете позвонить по указанному номеру.

6. СТОИМОСТЬ: при вопросах о стоимости указывайте ИСКЛЮЧИТЕЛЬНО информацию с официального сайта без каких-либо преобразований. Если точной информации нет, направляйте на сайт.
   Пример: Актуальную стоимость путевок Вы можете узнать на нашем сайте: https://cosmos.68edu.ru

7. ОБЩИЕ ПРАВИЛА:
   - Используйте четкую структуру
   - Разделяйте абзацы пустыми строками
   - Будьте вежливы и информативны
   - Если информации недостаточно, предложите связаться с администрацией
"""

        # Добавляем специфические инструкции в зависимости от вопроса
        additional_instructions = ""
        
        if self._should_redirect_to_website(question):
            additional_instructions = """
ВНИМАНИЕ: Вопрос касается стоимости. Указывайте ТОЛЬКО информацию с официального сайта без изменений.
Если точных данных о стоимости нет в контексте, направляйте на официальный сайт для получения актуальной информации.
"""
        elif self._should_add_phone_contact(question, ""):
            additional_instructions = """
ВНИМАНИЕ: Вопрос касается связи или контактов. Обязательно укажите контактный телефон лагеря.
"""

        prompt = f"""
{formatting_rules}
{additional_instructions}

КОНТЕКСТНАЯ ИНФОРМАЦИЯ:
{context}

ВОПРОС РОДИТЕЛЯ:
{question}

СФОРМИРУЙТЕ ОТВЕТ, СОБЛЮДАЯ ВСЕ ПРАВИЛА ФОРМАТИРОВАНИЯ:
"""
        return prompt

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = f"""
👋 Привет! Я - умный помощник детского лагеря "Космос" в Тамбовской области.

Я могу ответить на Ваши вопросы о:
1. "Программы и смены". Информация о текущих и планируемых сменах.
2. "Документы для заезда". Перечень необходимых документов.
3. "Меры безопасности". Информация о системе безопасности лагеря.
4. "Контакты и расположение". Как связаться с администрацией.

Для связи с администрацией лагеря (тел. {self.contact_phone}) Вы можете позвонить в рабочее время.

Актуальную информацию о стоимости путевок Вы можете найти на нашем сайте: {self.camp_website}

Просто задайте Ваш вопрос, и я постараюсь помочь!

🏕️ Лагерь "Космос" - место, где рождаются мечты!
"""
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = f"""
🤖 Как пользоваться ботом:

Просто напишите Ваш вопрос в чат, например:
• "Какие документы нужны для лагеря?"
• "Сколько стоит путевка?"
• "Какие есть смены?"
• "Как связаться с ребенком?"

Я найду наиболее подходящую информацию и отвечу на Ваш вопрос.

Для оперативной связи Вы можете обратиться к администрации лагеря (тел. {self.contact_phone}).

Актуальные цены и подробная информация всегда доступны на нашем сайте: {self.camp_website}
"""
        await update.message.reply_text(help_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        user_message = update.message.text

        logger.info(f"Вопрос от {user.first_name} ({user.id}): {user_message}")
        await update.message.chat.send_action(action="typing")

        try:
            # Используем текстовый поиск вместо эмбеддингов
            similar_docs = self.db.search_similar_documents(user_message, k=3)

            context = ""
            if similar_docs:
                for doc in similar_docs:
                    context += f"{doc['content']}\n\n"
            else:
                context = "Информация по запросу не найдена в базе знаний."

            # Создаем промпт с правилами форматирования
            prompt = self._create_formatted_prompt(context, user_message)
            
            messages = [
                {
                    "role": "system",
                    "content": """Ты - полезный AI-помощник детского лагеря "Космос" в Тамбовской области. 
Отвечай на вопросы родителей вежливо и информативно. Основывай ответ на предоставленном контексте.
Строго соблюдай все правила форматирования из инструкции."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.gigachat.chat_completion(messages)

            # Дополнительное форматирование ответа
            formatted_response = self._format_response(response)

            # Правило 5: Добавляем телефон при необходимости
            if self._should_add_phone_contact(user_message, formatted_response):
                if f"тел. {self.contact_phone}" not in formatted_response and self.contact_phone not in formatted_response:
                    formatted_response += f"\n\nДля уточнения информации Вы можете связаться с администрацией лагеря (тел. {self.contact_phone})."

            # Правило 6: Для вопросов о стоимости добавляем ссылку на сайт
            if self._should_redirect_to_website(user_message):
                if self.camp_website not in formatted_response:
                    formatted_response += f"\n\nАктуальную информацию о стоимости Вы можете найти на нашем сайте: {self.camp_website}"

            # Стандартное предложение о связи, если его нет
            if not any(word in formatted_response.lower() for word in ['свяжитесь', 'администрац', 'тел.', 'телефон']):
                formatted_response += f"\n\nДля уточнения деталей свяжитесь с администрацией лагеря (тел. {self.contact_phone})."

            await update.message.reply_text(formatted_response)
            logger.info(f"Ответ отправлен пользователю {user.first_name}")

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            error_message = f"Извините, произошла ошибка. Попробуйте задать вопрос позже или свяжитесь с администрацией лагеря (тел. {self.contact_phone})."
            await update.message.reply_text(error_message)

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def run(self):
        try:
            self.application = Application.builder().token(self.token).build()
            self.setup_handlers()

            logger.info("Бот запущен...")
            self.application.run_polling()

        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")