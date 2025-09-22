from logging import basicConfig, StreamHandler

from idna.codec import StreamReader
from sqlalchemy.testing.plugin.plugin_base import config
from sqlalchemy.testing.suite.test_reflection import metadata

from app.config import Config
from app.processing.data_parser import DataParser
from app.processing.db import DB
from app.agents.agent import GigaChatAgent
from app.bot.telegram_bot import TelegramBot
import logging
import os

logging,basicConfig(
    level= logging.INFO,
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers= [
        logging.FileHandler("bot.log"),
        logging,StreamHandler()
    ]
)

def main ():

    config = Config()
    parser = DataParser(config.CAMP_URL)
    website_data = parser.parse_website()

    vector_db = DB(config.API_KEY)

    if not os.path.exists("./data/chroma_db"):
        from langchain.docstore.document import Document
        documents = [Document(page_content=item['content'], metadata={"sourse":item['sourse']})
                     for item in website_data]
        vector_db.create_vector_db(documents)
    else:
       vector_db.load_vector_db()

    retriever = vector_db.get_retriever()
    agent = GigaChatAgent(config.API_KEY, retriever)

    bot = TelegramBot(config.BOT_TOKEN, agent)
    bot.run()

    if __name__ == "__main__":
        main()