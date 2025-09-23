# app/database/mysql_db.py
import mysql.connector
from mysql.connector import Error
import json
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MySQLVectorDB:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Установка соединения с MySQL"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("Успешное подключение к MySQL")
        except Error as e:
            logger.error(f"Ошибка подключения к MySQL: {e}")
            raise

    def _create_tables(self):
        """Создание необходимых таблиц"""
        try:
            cursor = self.connection.cursor()

            # Таблица для документов
            create_documents_table = """
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                content TEXT NOT NULL,
                source VARCHAR(255),
                chunk_index INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_source (source)
            )
            """

            # Таблица для эмбеддингов
            create_embeddings_table = """
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                document_id INT,
                embedding JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                INDEX idx_document_id (document_id)
            )
            """

            cursor.execute(create_documents_table)
            cursor.execute(create_embeddings_table)
            self.connection.commit()
            cursor.close()
            logger.info("Таблицы созданы успешно")

        except Error as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    def store_documents(self, documents):
        """Сохраняет документы и их эмбеддинги в базу"""
        try:
            cursor = self.connection.cursor()

            # Очищаем старые данные
            cursor.execute("DELETE FROM document_embeddings")
            cursor.execute("DELETE FROM documents")

            # Сохраняем документы
            for i, doc in enumerate(documents):
                # Вставляем документ
                insert_doc_query = """
                INSERT INTO documents (content, source, chunk_index)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_doc_query, (
                    doc['content'],
                    doc.get('source', 'unknown'),
                    i
                ))

                document_id = cursor.lastrowid

                # Сохраняем эмбеддинг
                if 'embedding' in doc:
                    insert_embed_query = """
                    INSERT INTO document_embeddings (document_id, embedding)
                    VALUES (%s, %s)
                    """
                    cursor.execute(insert_embed_query, (
                        document_id,
                        json.dumps(doc['embedding'])
                    ))

            self.connection.commit()
            cursor.close()
            logger.info(f"Успешно сохранено {len(documents)} документов")

        except Error as e:
            logger.error(f"Ошибка сохранения документов: {e}")
            self.connection.rollback()
            raise

    def search_similar_documents(self, query_embedding, k=3):
        """Поиск похожих документов по эмбеддингу запроса"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Получаем все документы с эмбеддингами
            cursor.execute("""
                SELECT d.id, d.content, d.source, de.embedding
                FROM documents d
                JOIN document_embeddings de ON d.id = de.document_id
            """)

            documents = cursor.fetchall()
            cursor.close()

            if not documents:
                return []

            # Вычисляем косинусное сходство для каждого документа
            scored_docs = []
            for doc in documents:
                doc_embedding = json.loads(doc['embedding'])
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                scored_docs.append({
                    'content': doc['content'],
                    'source': doc['source'],
                    'similarity': similarity
                })

            # Сортируем по сходству и возвращаем топ-K
            scored_docs.sort(key=lambda x: x['similarity'], reverse=True)
            return scored_docs[:k]

        except Error as e:
            logger.error(f"Ошибка поиска документов: {e}")
            return []

    def _cosine_similarity(self, vec1, vec2):
        """Вычисление косинусного сходства между двумя векторами"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)

            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0

            return float(dot_product / (norm_vec1 * norm_vec2))
        except Exception as e:
            logger.error(f"Ошибка вычисления сходства: {e}")
            return 0.0

    def get_document_count(self):
        """Возвращает количество документов в базе"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Error as e:
            logger.error(f"Ошибка получения количества документов: {e}")
            return 0

    def close(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с MySQL закрыто")