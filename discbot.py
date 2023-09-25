import json
import requests

from datetime import datetime
from datetime import timezone

import message

class DiscussionsBot(message.Message):
    def __init__(self, username, password, wikilink):
        self.session = requests.Session()
        self.wikiAPI = wikilink + 'api.php'
        self.wikiPHP = wikilink + 'wikia.php'

        self.headers = {
            'User-Agent': 'DiscussionsBot',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive'
        }

        self.username = username.replace('_', ' ')
        self.userID = self.__login(password)

        self.wikiID = self.__getWikiID()
        self.wikilang = self.__getWikilang()
        self.wikilink = wikilink

    def __login(self, password):
        ''' входит в аккаунт Фэндома и возвращает ID участника-бота '''

        loginData = {
            'username': self.username,
            'password': password
        }

        url = 'https://services.fandom.com/mobile-fandom-app/fandom-auth/login'
        response = self.session.post(url, data=loginData, headers=self.headers)
        print('Входим в аккаунт:', response)

        content = response.json()
        return int(content['user_id']) # договеренность: все числовые константы должны быть int

    def __OLDlogin(self, username, password):
        ''' старый метод, который использовался до ноябрьского обновления, чтобы зайти в аккаунт,
            вместо него используйте __login(username, password) выше '''

        tokenData = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }

        response = self.session.get(self.wikiAPI, params=tokenData, headers=self.headers)
        content = response.json()

        loginData = {
            'action': 'login',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': content['query']['tokens']['logintoken'],
            'format': 'json'
        }

        response = self.session.post(self.wikiAPI, data=loginData)

    def __getWikiID(self):
        payload = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'variables',
            'format': 'json'
        }

        response = self.session.get(self.wikiAPI, params=payload, headers=self.headers)
        content = response.json()
        return content['query']['variables'][1]['*'] # wgCityId

    def __getWikilang(self):
        return 'RU' # todo: бот должен забирать язык из настроек Фэндома

    def getWikiActivity(self, since, dir='older', limit=100):
        ''' симбиоз методов getRecentChanges() и getSocialActivity() '''

        # dir='older' возвращает правки/сообщения от новых, переходя к старым
        # dir='newer' возвращает правки/сообщения от старых, переходя к новым
        # limit=100 это максимальное значение

        changes = self.getRecentChanges(since, limit=limit)
        posts = self.getSocialActivity(since, limit=limit)
        edits = []

        # миллисекунды в someEdit['timestamp'] добавляются в угоду прихоти API Discussions, без них параметр since будет некорректно работать
        # для API MediaWiki они необязательны, но и не мешают корректному отображению правок

        for i in changes:
            someEdit = {
                'containerType': 'PAGE',
                'title': i['title'],
                'threadID': i['pageid'], # pageID
                'postID': i['rcid'],
                'forumID': i['ns'],
                'forumName': i['type'],
                'username': i['user'],
                'userID': i['userid'],
                'badgePermission': '',
                'timestamp': i['timestamp'][:-1] + '.000Z',
                'epochSecond': int(datetime.strptime(i['timestamp'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()), # timestamp() is float
                'jsonModel': '',
                'rawContent': '',
                'atMentions': [],
                'href': self.wikilink + 'wiki/' + i['title'].replace(' ', '_')
            }

            edits.append(someEdit)

        for i in posts:
            someEdit = {
                'containerType': i['_embedded']['thread'][0]['containerType'],
                'title': i['_embedded']['thread'][0]['title'],
                'threadID': int(i['threadId']), # договеренность: все числовые константы должны быть int
                'postID': int(i['id']),
                'forumID': int(i['forumId']),
                'forumName': i['forumName'],
                'username': i['createdBy']['name'],
                'userID': int(i['createdBy']['id']),
                'badgePermission': i['createdBy']['badgePermission'],
                'timestamp': datetime.fromtimestamp(i['creationDate']['epochSecond'], timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'epochSecond': i['creationDate']['epochSecond'],
                'jsonModel': i['jsonModel'],
                'rawContent': i['rawContent'],
                'atMentions': i['_embedded']['attachments'][0]['atMentions'],
                'href': self.wikilink
            }

            if someEdit['containerType'] == 'FORUM':
                # пример ссылки: https://warriors-cats.fandom.com/ru/f/p/threadID/r/postID
                someEdit['href'] += 'f/p/{}'.format(someEdit['threadID'])

                if i['position'] > 1: # 'position'=1 имеют только что созданные темы
                    someEdit['href'] += '/r/{}'.format(someEdit['postID'])

            elif someEdit['containerType'] == 'WALL':
                # пример ссылки: https://warriors-cats.fandom.com/ru/wiki/Message_Wall:Northshine?threadId=threadID#postID
                # ключ 'forumName' на стенах обсуждений имеет такое значение: 'Bottovodstvo Message Wall'
                someEdit['href'] += 'wiki/Message_Wall:{}?threadId={}'.format(someEdit['forumName'][:-13].replace(' ', '_'), someEdit['threadID'])

                if i['position'] > 1: # 'position'=1 имеют только что созданные темы
                    someEdit['href'] += '#{}'.format(someEdit['postID'])

            if someEdit['containerType'] == 'ARTICLE_COMMENT':
                # пример ссылки: https://warriors-cats.fandom.com/ru/wiki/Воинский_закон?commentId=threadID&replyId=postID
                someEdit['title'] = self.getArticleTitle(someEdit['forumID'])
                someEdit['href'] += 'wiki/{}?commentId={}'.format(someEdit['title'].replace(' ', '_'), someEdit['threadID'])

                if i['position'] > 1: # 'position'=1 имеют только что созданные темы
                    someEdit['href'] += '&replyId={}'.format(someEdit['postID'])

            edits.append(someEdit)

        edits.sort(key=lambda dict: dict['epochSecond']) # сортируем от старых правок/сообщений к новым по UNIX-времени

        if dir == 'older':
            posts.reverse()

        return edits

    def getRecentChanges(self, since, dir='older', limit=500):
        # https://warriors-cats.fandom.com/ru/api.php?action=query&list=recentchanges&rcend=2022-08-14T18:00:00.000Z&rcdir=older&rcprop=user|userid|timestamp|title|ids&rcshow=!anon|!bot&rclimit=500

        # dir='older' возвращает правки от новых, переходя к старым
        # dir='newer' возвращает правки от старых, переходя к новым
        # limit=500 это максимальное значение, см. документацию API:RecentChanges

        payload = {
            'action': 'query',
            'list': 'recentchanges',
            'rcdir': dir,
            'rcprop': 'user|userid|timestamp|title|ids',
            'rcshow': '!anon|!bot', # бот обсуждений игнорирует правки от анонимных участников и других ботов
            'rclimit': str(limit),
            'format': 'json'
        }

        # из-за особенностей API MediaWiki, см. их документацию API:RecentChanges
        if dir == 'older':
            payload['rcend'] = since
        elif dir == 'newer':
            payload['rcstart'] = since

        response = self.session.get(self.wikiAPI, params=payload, headers=self.headers)
        content = response.json()
        return content['query']['recentchanges']

    def getSocialActivity(self, since, dir='older', limit=100):
        # https://warriors-cats.fandom.com/ru/wikia.php?controller=DiscussionPost&method=getPosts&since=2022-08-14T18:00:00.000Z

        # dir='older' возвращает сообщения от новых, переходя к старым
        # dir='newer' возвращает сообщения от старых, переходя к новым
        # limit=100 это максимальное значение

        payload = {
            'controller': 'DiscussionPost',
            'method': 'getPosts',
            'limit': str(limit),
            'since': since # этот параметр корректно работает только, если будет такой формат даты: 2022-08-14T18:00:00.000Z (с миллисекундами!)
        }

        response = self.session.get(self.wikiPHP, params=payload, headers=self.headers)
        content = response.json()
        posts = content['_embedded']['doc:posts']

        # удаляем сообщения/комментария от анонимных участников (у них ID равно нулю) и от нашего бота
        # for i in tuple(posts):
        #     if i['createdBy']['id'] == '0' or i['createdBy']['id'] == str(self.userID):
        #         posts.remove(i)

        if dir == 'newer':
            posts.reverse()

        return posts

    def getUserContributions(self, userID, dir='older', limit=10):
        # https://warriors-cats.fandom.com/ru/api.php?action=query&list=usercontribs&limit=10&ucuserids=29565603&ucdir=older

        # dir='older' возвращает правки от новых, переходя к старым
        # dir='newer' возвращает правки от старых, переходя к новым
        # limit=10 это НЕ максимальное значение, но обычно больше десяти правок и не нужно :)

        payload = {
            'action': 'query',
            'list': 'usercontribs',
            'uclimit': str(limit),
            'ucuserids': str(userID),
            'ucdir': dir,
            'format': 'json'
        }

        response = self.session.get(self.wikiAPI, params=payload, headers=self.headers)
        content = response.json()
        return content['query']['usercontribs']

    def getUserProfileActivity(self, userID, dir='older', limit=10):
        # dir='older' возвращает сообщения от новых, переходя к старым
        # dir='newer' возвращает сообщения от старых, переходя к новым
        # limit=10 это НЕ максимальное значение, но обычно больше десяти сообщений и не нужно :)

        content = self.getFullUserProfileActivity(userID, limit=limit)
        posts = content['_embedded']['doc:posts']

        if dir == 'newer':
            posts.reverse()

        return posts[:limit]

    def getFirstUserContributions(self, userID):
        firstContibution = self.getUserContributions(userID, dir='newer', limit=1)

        if firstContibution:
            return firstContibution[0]

            return None

    def getFirstUserProfileActivity(self, userID):
        content = self.getFullUserProfileActivity(userID, limit=1)

        # если у участника отсутствует ссылка на последнюю страницу его социальной активности, то скаченная страница — и есть последняя
        if content['_links'].get('last'):
            response = self.session.get(content['_links']['last'][0]['href'], headers=self.headers)
            content = response.json()

        if content['_embedded']['doc:posts']:
            return content['_embedded']['doc:posts'][-1]

        return None

    def getFullUserProfileActivity(self, userID, limit=10):
        ''' особенный метод, аналога которого нет для правок на MediaWiki, порой нужно знать не просто первое или последнее сообщение,
            а всю страницу участника; через этот метод работают getUserProfileActivity() и getFirstUserProfileActivity() '''

        # https://warriors-cats.fandom.com/ru/wikia.php?controller=DiscussionContribution&method=getPosts&userId=29565603
        # limit=10 это НЕ максимальное значение, но обычно больше десяти сообщений и не нужно :)

        payload = {
            'controller': 'DiscussionContribution',
            'method': 'getPosts',
            'userId': str(userID),
            'limit': str(limit)
        }

        response = self.session.get(self.wikiPHP, params=payload, headers=self.headers)
        content = response.json()
        return content

    def getArticleTitle(self, forumId):
        # https://warriors-cats.fandom.com/ru/wikia.php?controller=ArticleComments&method=getArticleTitle&stablePageId=1

        payload = {
            'controller': 'ArticleComments',
            'method': 'getArticleTitle',
            'stablePageId': str(forumId)
        }

        response = self.session.get(self.wikiPHP, params=payload, headers=self.headers)
        content = response.json()
        return content['title']
