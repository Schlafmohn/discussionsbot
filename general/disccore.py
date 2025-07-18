import time
import random
import requests

from typing import Optional
from datetime import datetime, timezone
from http.cookiejar import LWPCookieJar

class DiscussionsCore:
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

        self._api_url = self.wikilink + '/api.php'
        self._wikia_api_url = self.wikilink + '/wikia.php'
    
    def _login(self, username: str, password: str) -> None:
        self.__cookie_jar = LWPCookieJar('configs/cookies.json')
        self._session.cookies = self.__cookie_jar

        try:
            self.__cookie_jar.load(ignore_discard=True)

        except FileNotFoundError:
            url = 'https://services.fandom.com/mobile-fandom-app/fandom-auth/login'

            data = {
                'username': username,
                'password': password
            }

            self._session.post(url, data=data, headers=self._headers)
            self.__cookie_jar.save(ignore_discard=True)
    
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

        # данные для участника-бота находятся в userinfo
        self.botname = data['query']['userinfo']['name']
        self.bot_id = data['query']['userinfo']['id']

        # данные для вики находятся в sitename
        self.wikiname = data['query']['general']['sitename']
        self.wikilang = data['query']['general']['lang']
        self.wikilink = data['query']['general']['server'] + data['query']['general']['scriptpath']

        # а вот с ID вики намного сложнее, оно находится в wgCityId
        self.wiki_id = data['query']['variables'][1]['*']
    
    def _get(self, url: str, params: dict) -> dict:
        response = self._session.get(url, params=params, headers=self._headers)
        print('[{}] [{}] GET Request {}'.format(self._get_time_now(), response.status_code, response.url))

        self.__cookie_jar.save(ignore_discard=True)
        time.sleep(random.uniform(1.2, 2.0))
        return response.json()
    
    def _post(self, url: str, params: dict, data: Optional[dict]=None) -> None:
        data = data if data is not None else {}
        response = self._session.post(url, params=params, data=data, headers=self._headers)
        print('[{}] [{}] POST Request'.format(self._get_time_now(), response.status_code))

        self.__cookie_jar.save(ignore_discard=True)
        time.sleep(random.uniform(2.4, 3.9))
    
    def _get_time_now(self):
        return datetime.now(timezone.utc).isoformat()
