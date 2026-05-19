import requests

BASE_URL = 'https://www.elfinanciero.com.mx'

def get_collection(collection_id, site='elfinanciero', from_=0, size=10):
    url = f'{BASE_URL}/pf/api/v3/content/fetch/content-api-collections'
    params = {
        'query': f'{{"from":{from_},"site":"{site}","size":{size},"id":"{collection_id}"}}',
        'd': '350',
        'mxId': '00000000',
        '_website': site
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_article(article_id, site='elfinanciero'):
    url = f'{BASE_URL}/pf/api/v3/content/fetch/content-api-items'
    params = {
        'query': f'{{"id":"{article_id}","site":"{site}"}}',
        'd': '350',
        'mxId': '00000000',
        '_website': site
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def search(query, site='elfinanciero', from_=0, size=10):
    url = f'{BASE_URL}/pf/api/v3/content/fetch/content-api-search'
    params = {
        'query': f'{{"q":"{query}","from":{from_},"site":"{site}","size":{size}}}',
        'd': '350',
        'mxId': '00000000',
        '_website': site
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()