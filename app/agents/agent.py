from enum import verify
from venv import logger

from langchain.chains import RetrievalQA
from  langchain.llms import GigaChat
from langchain.prompts import PromptTemplate
import logging

from langsmith.schemas import Prompt
from sqlalchemy import false

logger = logging.getLogger(__name__)

class GigaChatAgent:

    def __init__(self, api_key, retriever):
        self.llm = GigaChat(
            credentials = api_key,
            verify_ssl = false
        )
        self.retriever = retriever

        self.promt_template =" " #шаблон промта

        self.qa_chain = self._create_chain()

    def _create_chain(self):
        Prompt = PromptTemplate(
            template = self.promt_template,
            input_variables = ["context", "question"]
        )
        return RetrievalQA.from_chain_type(
            llm = self.llm,
            chain_type = "stuff",
            retriever = self.retriever,
            chain_type_kwargs = {"prompt": Prompt},
            return_source_documents = True
        )
    def get_answer (self,question):

        result = self.qa_chain({"query":question})
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result['result']}")
        logger.info(f"Sourse documents:{result['sourse_documents']}")

        return result ['result']

