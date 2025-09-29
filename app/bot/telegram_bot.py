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
        self.contact_email = "kosmos@OBRAZ.TAMBOV.GOV.RU"
        self.camp_website = "https://cosmos.68edu.ru"

    def _format_response(self, response):
        """Форматирует ответ согласно правилам"""
        
        # Правило 6: Обращения "Вам", "Вы" с заглавной буквы
        response = re.sub(r'\bвам\b', 'Вам', response)
        response = re.sub(r'\bвы\b', 'Вы', response)
        response = re.sub(r'\bВаш\b', 'Ваш', response)
        response = re.sub(r'\bваш\b', 'Ваш', response)
        
        # Убираем логику мышления (Правило 5)
        thinking_phrases = [
            'я думаю', 'по моему мнению', 'с точки зрения логики',
            'я считаю', 'на мой взгляд', 'исходя из этого',
            'таким образом', 'следовательно', 'итак'
        ]
        for phrase in thinking_phrases:
            response = re.sub(phrase, '', response, flags=re.IGNORECASE)
        
        # Убираем лишние пробелы после обработки
        response = re.sub(r'\s+', ' ', response)
        response = re.sub(r'\n\s*\n', '\n\n', response)
        
        return response.strip()

    def _should_add_contacts(self, question):
        """Определяет, нужно ли добавлять контактные данные"""
        contact_keywords = [
            'связь', 'связаться', 'контакт', 'телефон', 'позвонить', 'звонок',
            'администрация', 'руководство', 'директор', 'начальник',
            'ребенок', 'дети', 'сын', 'дочь', 'позвонить ребенку',
            'связь с ребенком', 'связаться с детьми', 'общение с детьми',
            'родительский день', 'посещение', 'встреча', 'почта', 'email'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in contact_keywords)

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
ПРИ ФОРМИРОВАНИИ ОТВЕТА СТРОГО СОБЛЮДАЙТЕ СЛЕДУЮЩИЕ ПРАВИЛА ФОРМАТИРОВАНИЯ:

1. ССЫЛКИ НА САЙТ:
   - Ссылки пишутся без кавычек и других символов выделения
   - Ссылка ставится через пробел после двоеточия, следующего за упоминанием ресурса
   - Ссылки вставляются ИСКЛЮЧИТЕЛЬНО в конце предложения
   Пример: Актуальную информацию Вы можете найти на нашем сайте: https://cosmos.68edu.ru

2. АДРЕСА ЭЛЕКТРОННОЙ ПОЧТЫ:
   - Email указывается без кавычек и других символов выделения
   Пример: По всем вопросам пишите на email: kosmos@OBRAZ.TAMBOV.GOV.RU

3. КОНТАКТНЫЕ ДАННЫЕ:
   - При вопросах о связи с представителями лагеря или контакте с детьми ОБЯЗАТЕЛЬНО указывайте телефон и почту
   - Контактный телефон указывается в круглых скобках при упоминании администрации
   Пример: Для связи с администрацией лагеря (тел. +7 (4752) 55-70-09) Вы можете использовать указанный номер.

4. ПЕРЕЧИСЛЕНИЯ:
   - Используются ТОЛЬКО при строгой необходимости и когда пунктов больше одного
   - НЕ используйте для контактов представителей лагеря
   - Формат:
     [пустая строка]
     1. "Название пункта". 
     Описание пункта с новой строки.
     [пустая строка]
     2. "Второй пункт". 
     Описание второго пункта.
     [пустая строка после последнего пункта]

5. СОДЕРЖАНИЕ ОТВЕТА:
   - НЕ описывайте логику своего мышления
   - Давайте только информацию, непосредственно касающуюся ответа
   - Используйте перечисления только при необходимости

6. ОБРАЩЕНИЯ:
   - "Вам", "Вы", "Ваш" всегда пишутся с заглавной буквы

7. СТОИМОСТЬ:
   - Указывайте ИСКЛЮЧИТЕЛЬНО информацию с официального сайта без преобразований
   - Если точных данных нет, направляйте на официальный сайт

8. ЦИТАТЫ И НАЗВАНИЯ:
   - Все цитаты и названия указывайте в двойных кавычках
   Пример: Программа "Космические приключения" включает...

ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ:
- Будьте вежливы и информативны
- Используйте четкую структуру ответа
- Разделяйте абзацы пустыми строками
- Если информации недостаточно, предложите связаться с администрацией
"""

        # Добавляем специфические инструкции в зависимости от вопроса
        additional_instructions = ""
        
        if self._should_redirect_to_website(question):
            additional_instructions = """
ВНИМАНИЕ: Вопрос касается стоимости. 
- Указывайте ТОЛЬКО информацию с официального сайта БЕЗ ИЗМЕНЕНИЙ
- Если точных данных о стоимости нет в контексте, направляйте на официальный сайт
- Ссылку на сайт размещайте в конце предложения
"""
        elif self._should_add_contacts(question):
            additional_instructions = """
ВНИМАНИЕ: Вопрос касается связи или контактов.
- ОБЯЗАТЕЛЬНО укажите контактный телефон: +7 (4752) 55-70-09
- ОБЯЗАТЕЛЬНО укажите email: kosmos@OBRAZ.TAMBOV.GOV.RU
- Телефон указывайте в круглых скобках при упоминании администрации
- НЕ оформляйте контакты в виде списка
"""

        prompt = f"""
{formatting_rules}
{additional_instructions}

КОНТЕКСТНАЯ ИНФОРМАЦИЯ ДЛЯ ФОРМИРОВАНИЯ ОТВЕТА:
{context}

ВОПРОС РОДИТЕЛЯ:
{question}

СФОРМИРУЙТЕ ОТВЕТ, СТРОГО СОБЛЮДАЯ ВСЕ ВЫШЕУКАЗАННЫЕ ПРАВИЛА ФОРМАТИРОВАНИЯ.
ОТВЕТ ДОЛЖЕН БЫТЬ ПОЛЕЗНЫМ, ИНФОРМАТИВНЫМ И СООТВЕТСТВОВАТЬ ВСЕМ ПРАВИЛАМ:
"""
        return prompt

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = f"""
👋 Привет! Я - умный помощник детского лагеря "Космос" в Тамбовской области.

Я могу ответить на Ваши вопросы о:
1. "Программы и смены". 
Информация о текущих и планируемых сменах.

2. "Документы для заезда". 
Перечень необходимых документов.

3. "Меры безопасности". 
Информация о системе безопасности лагеря.

4. "Контакты и расположение". 
Как связаться с администрацией.

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
СТРОГО СОБЛЮДАЙ все правила форматирования из инструкции. Не описывай логику своего мышления."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.gigachat.chat_completion(messages)

            # Дополнительное форматирование ответа
            formatted_response = self._format_response(response)

            # Правило 3: Добавляем контакты при необходимости
            if self._should_add_contacts(user_message):
                contacts_added = False
                # Проверяем, есть ли уже контакты в ответе
                if self.contact_phone not in formatted_response:
                    formatted_response += f"\n\nДля уточнения информации Вы можете связаться с администрацией лагеря (тел. {self.contact_phone})."
                    contacts_added = True
                if self.contact_email not in formatted_response:
                    if contacts_added:
                        formatted_response += f" Также Вы можете написать на email: {self.contact_email}"
                    else:
                        formatted_response += f"\n\nВы можете написать на email: {self.contact_email}"

            # Правило 7: Для вопросов о стоимости добавляем ссылку на сайт
            if self._should_redirect_to_website(user_message):
                if self.camp_website not in formatted_response:
                    formatted_response += f"\n\nАктуальную информацию о стоимости Вы можете найти на нашем сайте: {self.camp_website}"

            # Стандартное предложение о связи, если его нет и вопрос не о стоимости
            if not self._should_redirect_to_website(user_message) and not any(word in formatted_response.lower() for word in ['свяжитесь', 'администрац', 'тел.', 'телефон', 'email']):
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