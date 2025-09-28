# app/bot/telegram_bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, gigachat_client, database):
        self.token = token
        self.gigachat = gigachat_client
        self.db = database
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
        👋 Привет! Я - умный помощник детского лагеря "Космос" в Тамбовской области.

        Я могу ответить на ваши вопросы о:
        • Программах и сменах
        • Документах для заезда
        • Мерах безопасности
        • Контактах и расположении

        Просто задайте ваш вопрос, и я постараюсь помочь!

        🏕️ Лагерь "Космос" - место, где рождаются мечты!
        """
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
        🤖 Как пользоваться ботом:

        Просто напишите ваш вопрос в чат, например:
        • "Какие документы нужны для лагеря?"
        • "Сколько стоит путевка?"
        • "Какие есть смены?"

        Я найду наиболее подходящую информацию и отвечу на ваш вопрос.

        Если нужна дополнительная помощь, звоните администрации лагеря.
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

            messages = [
                {
                    "role": "system",
                    "content": """Ты - полезный AI-помощник детского лагеря "Космос" в Тамбовской области. 
Отвечай на вопросы родителей вежливо и информативно. Основывай ответ на предоставленном контексте.
Если информации в контексте недостаточно, предложи связаться с администрацией лагеря для уточнения."""
                },
                {
                    "role": "user",
                    "content": f"""Контекстная информация:
{context}

Вопрос родителя: {user_message}

Ответ:"""
                }
            ]

            response = self.gigachat.chat_completion(messages)

            if "свяжитесь" not in response.lower() and "администрац" not in response.lower():
                response += "\n\nДля уточнения деталей свяжитесь с администрацией лагеря."

            await update.message.reply_text(response)
            logger.info(f"Ответ отправлен пользователю {user.first_name}")

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text("Извините, произошла ошибка. Попробуйте задать вопрос позже.")

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