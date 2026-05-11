"""DeepSeek API client with retry logic, timeout enforcement, and structured logging."""
import os, sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trevor_config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT_SECONDS, DEEPSEEK_MAX_RETRIES
from trevor_log import get_logger

log = get_logger("deepseek_client")

BASE_URL = DEEPSEEK_BASE_URL
API_KEY = DEEPSEEK_API_KEY
MODEL = DEEPSEEK_MODEL


class DeepSeekClient:
    def __init__(self, timeout=None, max_retries=None):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.model = MODEL
        self.timeout = timeout or DEEPSEEK_TIMEOUT_SECONDS
        self.max_retries = max_retries or DEEPSEEK_MAX_RETRIES

    def chat(self, prompt: str, system: str = 'You are an intelligence analysis system.'):
        if not self.api_key:
            log.error("DEEPSEEK_API_KEY not set")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 8192,
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                with log.start_task(f"deepseek_chat_{self.model}"):
                    r = requests.post(
                        f'{self.base_url}/chat/completions',
                        headers=headers,
                        json=payload,
                        timeout=self.timeout,
                    )
                    r.raise_for_status()
                    result = r.json()['choices'][0]['message']['content']
                    log.info("DeepSeek response received", model=self.model,
                             input_tokens=r.json().get('usage',{}).get('prompt_tokens',0),
                             output_tokens=r.json().get('usage',{}).get('completion_tokens',0))
                    return result
            except requests.Timeout:
                last_error = f"Timeout after {self.timeout}s (attempt {attempt+1}/{self.max_retries+1})"
                log.warning(last_error, model=self.model)
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else "?"
                last_error = f"HTTP {status}: {e}"
                log.warning(last_error, model=self.model, attempt=attempt)
                if status == 429:
                    import time
                    time.sleep(2 ** attempt)  # exponential backoff
            except Exception as e:
                last_error = str(e)
                log.error(last_error, model=self.model, attempt=attempt)

        log.error("All retries exhausted", model=self.model, last_error=last_error)
