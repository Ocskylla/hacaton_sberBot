from sqlalchemy.orm.sync import update
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, ApplicationBuilder
import logging
from app.agents.agent import GigaChatAgent

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, gigachat_agent):
        self.token = token
        self.gigachat_agent = gigachat_agent
        self.application = Application.builder().token(self.token). build()

        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filtetrs.COMMAND, self.handle_message))

    async def start_command (self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = "welcome"
        await update.message.reply_text(welcome_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        response = self.gigachat_agent.get_answer(user_message)
        await update.message.reply_text(response)

    def run (self):
        logger.info("bot started...")
        self.application.run_polling()
