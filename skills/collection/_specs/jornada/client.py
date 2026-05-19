import requests

BASE_URL = 'https://www.jornada.com.mx'

def get_article(slug):
    url = f'{BASE_URL}/articledata/{slug}'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_suplementos():
    url = f'{BASE_URL}/serviciosjornada/microservicios/jornada/suplementos.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_especiales():
    url = f'{BASE_URL}/serviciosjornada/microservicios/pdf/especiales.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()