from socket import send_fds

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import GigaChatEmbeddings
from langchain.vectorstores import  Chroma
import json

class DB:
    def __init__(self, api_key):
        self.embeddings = GigaChatEmbeddings( credentials = api_key, verify_ssl = False)
        self.vectorstore = None

    def crate_db (self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        self.vectorstore = Chroma.from_documents(
            documents =texts,
            embedding = self.embeddings,
            persist_derictory = "./data/chroma_db"
        )

        def load_db (self):
            self.vectorstore = Chroma(
                persist_directory = "./data/chroma_db",
                embedding_functions = self.embeddings
            )

            def get_retriever(self):
                return self.vectorstore.as_retriever (search_kwargs = {"k" : 3})
