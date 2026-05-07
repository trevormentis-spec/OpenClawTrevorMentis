import os
import requests

BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
API_KEY = os.getenv('DEEPSEEK_API_KEY')
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')


class DeepSeekClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.model = MODEL

    def chat(self, prompt:str, system:str='You are an intelligence analysis system.'):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role':'system','content':system},
                {'role':'user','content':prompt}
            ],
            'temperature':0.3
        }

        r = requests.post(
            f'{self.base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=180
        )

        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
