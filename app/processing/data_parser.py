from http.client import responses

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

class DataParser:
    def __init__(self, base_url):
        self.base_url = base_url

    def parse_website(self):
        pages_to_parse = ['/about', '/programs', '/parents', '/documents', '/safety']
        all_data = []

        for page in pages_to_parse:
            response = requests.get(self.base_url + page)
            soup = BeautifulSoup (response.text, 'html.parser')
            text = soup.get_text (separator = ' ', strip = True)
            all_data.append({
                'sourse': page,
                'content':text[5000]
            })
            return all_data

        def load_faq (self, faq_path):
            #загрузка
            pass