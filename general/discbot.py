import requests
from typing import Optional

class DiscussionsBot():
    def __init__(self, username: str, password: str, wikilink: str):
        self._session = requests.Session()

        self._headers = {
            'User-Agent': 'Discussions Bot v0.1 14 July, 2025',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest'
        }

        self._login(username, password) # заходим в аккаунт участника-бота
        self._get_meta_info(wikilink) # получаем метаданные о себе и о вики, на которой будем работать

        self._api_url = self._wikilink + '/api.php'
        self._wikia_api_url = self._wikilink + '/wikia.php'
    
    def _login(self, username: str, password: str) -> None:
        url = 'https://services.fandom.com/mobile-fandom-app/fandom-auth/login'

        data = {
            'username': username,
            'password': password
        }

        self._session.post(url, data=data, headers=self._headers)
        print('зашли в аккаунт')
    
    def _get_meta_info(self, wikilink: str) -> None:
        ''' для корректной работы бота обсуждений нужны следующие данные:
            - верное название участника-бота (непонятно, что в config.json находится)
            - ID участника-бота
            - верно название вики
            - язык вики (русский, английский, польский)
            - и верный URL вики (да, я настолько даже себе не доверяю) '''

        parameters = {
            'action': 'query',
            'meta': 'userinfo|siteinfo',
            'siprop': 'general|variables',
            'format': 'json'
        }

        data = self._get(wikilink + 'api.php', params=parameters)

        # данные для участника-бота находятся в `userinfo`
        self._botname = data['query']['userinfo']['name']
        self._bot_id = data['query']['userinfo']['id']

        # данные для вики находятся в `sitename`
        self._wikiname = data['query']['general']['sitename']
        self._wikilang = data['query']['general']['lang']
        self._wikilink = data['query']['general']['server'] + data['query']['general']['scriptpath']

        # а вот с ID вики намного сложнее, оно находится в `wgCityId`
        self._wiki_id = data['query']['variables'][1]['*']
        print('получили метаданные')
    
    def _get(self, url: str, params: dict) -> dict:
        response = self._session.get(url, params=params, headers=self._headers)
        response.raise_for_status()
        return response.json()
    
    def _post(self, url: str, params: dict, data: Optional[dict]=None) -> bool:
        try:
            data = data if data is not None else {}
            response = self._session.post(url, params=params, data=data, headers=self._headers)
            response.raise_for_status()
            return True
        
        except requests.RequestException:
            return False
