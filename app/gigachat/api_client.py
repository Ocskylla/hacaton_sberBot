# app/gigachat/api_client.py
import requests
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GigaChatClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.access_token = None
        self.token_expires = None

    def _authenticate(self):

        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return True

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(
                'https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
                headers=headers,
                data='scope=GIGACHAT_API_PERS',
                verify=False,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.token_expires = datetime.now() + timedelta(minutes=25)
                logger.info("Успешная аутентификация в GigaChat")
                return True
            else:
                logger.error(f"Ошибка аутентификации: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {e}")
            return False

    def get_embeddings(self, texts):
        if not self._authenticate():
            return None

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            data = {
                "model": "Embeddings",
                "input": texts
            }

            response = requests.post(
                f'{self.base_url}/embeddings',
                headers=headers,
                json=data,
                verify=False,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return [item['embedding'] for item in result['data']]
            else:
                logger.error(f"Ошибка получения эмбеддингов: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при получении эмбеддингов: {e}")
            return None

    def chat_completion(self, messages, temperature=0.7):

        if not self._authenticate():
            return "Извините, произошла ошибка при подключении к AI-сервису."

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            data = {
                "model": "GigaChat",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1024
            }

            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                verify=False,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"Ошибка чат-запроса: {response.status_code} - {response.text}")
                return "Извините, произошла ошибка при обработке запроса."

        except Exception as e:
            logger.error(f"Ошибка при отправке чат-запроса: {e}")
            return "Извините, произошла ошибка при подключении к AI-сервису."