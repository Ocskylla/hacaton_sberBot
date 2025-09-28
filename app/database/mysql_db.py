# app/database/mysql_db.py
import mysql.connector
from mysql.connector import Error
import json
import logging
from datetime import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import joblib
import os

logger = logging.getLogger(__name__)

class MySQLTextDB:
    def __init__(self, config):
        self.config = config
        self.connection = None
        
        # Исправляем инициализацию TfidfVectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000, 
            stop_words=list(russian_stop_words())  # Преобразуем в список
        )
        
        self.tfidf_matrix = None
        self.document_ids = []
        self._connect()
        self._create_tables()
        self._load_tfidf_model()

    def _connect(self):
        """Подключение к MySQL"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("✅ Успешное подключение к MySQL")
        except Error as e:
            logger.error(f"❌ Ошибка подключения к MySQL: {e}")
            raise

    def _create_tables(self):
        """Создание таблиц если они не существуют"""
        try:
            cursor = self.connection.cursor()

            create_documents_table = """
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                content TEXT NOT NULL,
                source VARCHAR(500),
                type VARCHAR(50),
                chunk_index INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                keywords TEXT,
                INDEX idx_source (source),
                INDEX idx_type (type),
                FULLTEXT idx_content (content)
            )
            """

            cursor.execute(create_documents_table)
            self.connection.commit()
            cursor.close()
            logger.info("✅ Таблицы созданы успешно")

        except Error as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise

    def _load_tfidf_model(self):
        """Загрузка или создание TF-IDF модели"""
        try:
            if os.path.exists('tfidf_model.pkl'):
                self.vectorizer = joblib.load('tfidf_model.pkl')
                self.tfidf_matrix = joblib.load('tfidf_matrix.pkl')
                self.document_ids = joblib.load('document_ids.pkl')
                logger.info("✅ TF-IDF модель загружена из файла")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить TF-IDF модель: {e}")

    def _save_tfidf_model(self):
        """Сохранение TF-IDF модели"""
        try:
            joblib.dump(self.vectorizer, 'tfidf_model.pkl')
            joblib.dump(self.tfidf_matrix, 'tfidf_matrix.pkl')
            joblib.dump(self.document_ids, 'document_ids.pkl')
            logger.info("✅ TF-IDF модель сохранена")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения TF-IDF модели: {e}")

    def _preprocess_text(self, text):
        """Предобработка текста"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_keywords(self, text, top_n=10):
        """Извлечение ключевых слов из текста"""
        words = re.findall(r'\b[а-яё]{3,}\b', text.lower())
        word_freq = {}
        for word in words:
            if word not in russian_stop_words():
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return ' '.join([word for word, freq in sorted_words[:top_n]])

    def store_documents(self, documents):
        """Сохранение документов в базу"""
        try:
            cursor = self.connection.cursor()

            # Очищаем старые данные
            cursor.execute("DELETE FROM documents")
            logger.info("🗑️ Очищены старые данные")

            stored_count = 0
            all_texts = []

            for i, doc in enumerate(documents):
                # Извлекаем ключевые слова
                keywords = self._extract_keywords(doc['content'])
                
                # Сохраняем документ
                insert_doc_query = """
                INSERT INTO documents (content, source, type, chunk_index, keywords)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_doc_query, (
                    doc['content'],
                    doc.get('source', 'unknown'),
                    doc.get('type', 'website'),
                    doc.get('chunk_index', 0),
                    keywords
                ))

                document_id = cursor.lastrowid
                stored_count += 1
                all_texts.append(self._preprocess_text(doc['content']))

            self.connection.commit()
            cursor.close()

            # Обучаем TF-IDF модель
            if all_texts:
                self.tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                self.document_ids = list(range(1, stored_count + 1))
                self._save_tfidf_model()

            logger.info(f"💾 Успешно сохранено документов: {stored_count}")
            return stored_count

        except Error as e:
            logger.error(f"❌ Ошибка сохранения документов: {e}")
            self.connection.rollback()
            raise

    def search_similar_documents(self, query, k=3):
        """Поиск похожих документов по текстовому запросу"""
        try:
            if self.tfidf_matrix is None or not self.document_ids:
                # Fallback: поиск по ключевым словам
                return self._keyword_search(query, k)

            # Преобразуем запрос в TF-IDF вектор
            query_vec = self.vectorizer.transform([self._preprocess_text(query)])
            
            # Вычисляем косинусное сходство
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Получаем топ-K документов
            top_indices = similarities.argsort()[-k:][::-1]
            
            cursor = self.connection.cursor(dictionary=True)
            similar_docs = []
            
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Порог сходства
                    doc_id = self.document_ids[idx]
                    cursor.execute("SELECT content, source, type FROM documents WHERE id = %s", (doc_id,))
                    doc = cursor.fetchone()
                    if doc:
                        similar_docs.append({
                            'content': doc['content'],
                            'source': doc['source'],
                            'type': doc['type'],
                            'similarity': float(similarities[idx])
                        })
            
            cursor.close()
            
            if not similar_docs:
                return self._keyword_search(query, k)
                
            logger.info(f"🔍 Найдено похожих документов: {len(similar_docs)}")
            return similar_docs

        except Exception as e:
            logger.error(f"❌ Ошибка поиска документов: {e}")
            return self._keyword_search(query, k)

    def _keyword_search(self, query, k=3):
        """Резервный поиск по ключевым словам"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Извлекаем ключевые слова из запроса
            query_keywords = self._extract_keywords(query, top_n=5)
            keywords_list = query_keywords.split()
            
            if not keywords_list:
                return []
            
            # Поиск по ключевым словам в содержимом
            conditions = []
            params = []
            for keyword in keywords_list:
                conditions.append("(content LIKE %s OR keywords LIKE %s)")
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            where_clause = " OR ".join(conditions)
            
            query_sql = f"""
            SELECT content, source, type
            FROM documents 
            WHERE {where_clause}
            LIMIT %s
            """
            
            params.append(k)
            cursor.execute(query_sql, params)
            docs = cursor.fetchall()
            
            formatted_docs = []
            for doc in docs:
                formatted_docs.append({
                    'content': doc['content'],
                    'source': doc['source'],
                    'type': doc['type'],
                    'similarity': 0.5  # Средняя релевантность для ключевого поиска
                })
            
            cursor.close()
            logger.info(f"🔍 Найдено документов по ключевым словам: {len(formatted_docs)}")
            return formatted_docs
            
        except Exception as e:
            logger.error(f"❌ Ошибка ключевого поиска: {e}")
            return []

    def get_document_count(self):
        """Получение количества документов"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Error as e:
            logger.error(f"❌ Ошибка получения количества документов: {e}")
            return 0

    def close(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Соединение с MySQL закрыто")

def russian_stop_words():
    """Русские стоп-слова"""
    return {
        'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она',
        'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее',
        'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда',
        'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до',
        'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей',
        'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем',
        'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет',
        'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним',
        'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда',
        'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть',
        'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая',
        'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед',
        'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно',
        'всю', 'между'
    }