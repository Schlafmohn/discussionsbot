import json
import requests

import discmess

from datetime import datetime, timezone

class DiscussionsBot():
    def __init__(self, botUsername, password, wikilink):
        self.__session = requests.Session()
        self.__apiRecentChanges = wikilink + '/api.php'
        self.__apiSocialActivity = wikilink + '/wikia.php'

        self.__headers = {
            'User-Agent': 'Discussions Bot v0.1 14 July, 2025',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest'
        }

        self.__botUsername = botUsername
        self.__botUserID = 1234

        self.__wikiID = self.__getWikiID()
        self.__login(password)
    
    def __login(self, password):
        url = 'https://services.fandom.com/mobile-fandom-app/fandom-auth/login'

        data = {
            'username': self.__botUsername,
            'password': password
        }

        response = self.__session.post(url, data=data, headers=self.__headers)
        print('[{}] [{}] Вошли в аккаунт участника-бота {} на Фэндоме'.format(
            self.__getDateTimeNow(),
            response.status_code,
            self.__botUsername
        ))

        self.__botUserID = int(response.json()['user_id'])
    
    def getWikiActivity(self, sinсe, limit=100):
        edits = self.getRecentChanges(sinсe, limit=limit)
        posts = self.getSocialActivity(sinсe, limit=limit)

        messages = edits + posts
        return sorted(messages, key=lambda item: item['timestamp'])
    
    def getRecentChanges(self, since, limit=100):
        payload = {
            'action': 'query',
            'list': 'recentchanges',
            'rcstart': since,
            'rcdir': 'newer', # список выводится от старых к новым правкам
            'rcexcludeuser': self.__botUsername, # игнорируем любые свои правки (от бота)
            'rcprop': 'user|userid|timestamp|title|ids',
            'rcshow': '!anon|!bot', # игнорируем любые правки от анонимных участников и от других ботов
            'rclimit': str(limit),
            'format': 'json'
        }

        response = self.__session.get(self.__apiRecentChanges, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили свежие правки на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            self.__apiRecentChanges
        ))


        content = response.json()
        return self.__helpRecentChanges(content['query']['recentchanges'])
    
    def getSocialActivity(self, since, limit=100):
        payload = {
            'controller': 'DiscussionPost',
            'method': 'getPosts',
            'limit': str(limit),
            'since': since[:-1] + '.000Z'
        }

        response = self.__session.get(self.__apiSocialActivity, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили социальную активность на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            self.__apiSocialActivity
        ))

        content = response.json()
        return self.__helpSocialActivity(content['_embedded']['doc:posts'])
    
    def getUserContributions(self, username=None, userID=None, limit=10):
        payload = {
            'action': 'query',
            'list': 'usercontribs',
            'uclimit': str(limit),
            'ucdir': 'newer', # список выводится от первой правки на вики
            'format': 'json'
        }

        if username:
            payload['ucuser'] = username
            telnetUser = username
        else:
            payload['ucuserids'] = userID
            telnetUser = str(userID)

        response = self.__session.get(self.__apiRecentChanges, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили вклад участника {} на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            telnetUser,
            self.__apiRecentChanges
        ))

        content = response.json()
        return self.__helpRecentChanges(content['query']['usercontribs'])
    
    def getUserProfileActivity(self, username=None, userID=None, limit=10):
        if not userID:
            userID = self.getUserID(username)

        payload = {
            'controller': 'DiscussionContribution',
            'method': 'getPosts',
            'userId': str(userID),
            'limit': str(limit)
        }

        response = self.__session.get(self.__apiSocialActivity, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили активность участника {} на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            userID,
            self.__apiSocialActivity
        ))

        content = response.json() # на самом деле, это более, чем бессмысленно, но пока, сейчас на стадии разработки, это более, чем хорошо
        return self.__helpSocialActivity(content['_embedded']['doc:posts'])
    
    def __helpRecentChanges(self, content):
        ''' преобразует вывод свежих правок или вклада участника к единому формату DiscussionsBot '''

        messages = []

        for i in content:
            messages.append({
                # возможные варианты: EDIT, NEW, LOG и CATEGORIZE
                'type': None, # сделано для совместимости с вкладом участника - там отсутствует этот ключ

                # название и ID страницы 
                'thread': i['title'],
                'threadID': i['pageid'],

                # ID правки к странице
                'postID': i['revid'],

                'user': i['user'],
                'userID': i['userid'],
                'timestamp': datetime.strptime(i['timestamp'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc),
                'pingDiscBot': False,

                'forum': None, # добавлен для совместимости, все страницы имеют значение None
                'forumID': i['ns']
            })

            if 'type' in i:
                messages[-1]['type'] = i['type'].upper()
            
            elif 'new' in i:
                messages[-1]['type'] = 'NEW'
            else:
                messages[-1]['type'] = 'EDIT'
        
        return messages
    
    def __helpSocialActivity(self, content):
        ''' преобразует вывод социальной активности или активности участника к единому формату DiscussionsBot '''

        messages = []

        for i in content:
            # игнорируем любые сообщения от анонимных участников (ID = 0) и свои же сообщения (от бота)
            # if i['createdBy']['id'] == '0' or i['createdBy']['id'] == str(self.__botUserID):
            #     continue

            messages.append({
                # возможные варианты: FORUM, WALL и ARTICLE_COMMENT
                'type': i['_embedded']['thread'][0]['containerType'],

                # название и ID темы (на форуме или на стене обсуждения) или страницы
                'thread': i['_embedded']['thread'][0]['title'],
                'threadID': int(i['threadId']),

                # ID сообщения к теме (на форуме или на стене обсуждения) или комментария на странице
                'postID': int(i['id']),

                'user': i['createdBy']['name'],
                'userID': int(i['createdBy']['id']),
                'timestamp': datetime.fromtimestamp(i['creationDate']['epochSecond'], tz=timezone.utc),
                'pingDiscBot': None,

                # в случае FORUM:           хранят название форума (каталога) и его ID
                # в случае WALL:            хранят имя участница и стену обсуждения, ID - непонятно
                # в случае ARTICLE_COMMENT: хранят None и ID страницы
                'forum': i['forumName'],
                'forumID': int(i['forumId'])
            })

            if not i['_embedded']['attachments'][0]['atMentions']:
                messages[-1]['pingDiscBot'] = False
            elif i['_embedded']['attachments'][0]['atMentions'] == str(self.__botUserID):
                messages[-1]['pingDiscBot'] = True
        
        messages.reverse() # список выводится от старых к новым сообщениям и комментариям
        
        return messages
    
    def createThreadDiscussions(self, message):
        pass
    
    def createThreadMessageWalk(self, message, title, username=None, userID=None):
        # https://discbot.fandom.com/ru/wikia.php?controller=Fandom\MessageWall\MessageWall&method=createThread&format=json

        if not userID:
            userID = self.getUserID(username)

        payload = {
            'controller': 'Fandom\MessageWall\MessageWall',
            'method': 'createThread',
            'format': 'json'
        }

        body = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'wallOwnerId': str(userID),
            'title': title,
            'rawContent': message.getRawContent(),
            'jsonModel': message.getJSONModel(),
            'attachments': message.getAttachments()
        }

        response = self.__session.post(self.__apiSocialActivity, params=payload, data=body, headers=self.__headers)
        print('[{}] [{}] Отправили сообщение на стену обсуждения участника {} на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            userID,
            self.__apiSocialActivity
        ))
    
    def createReplyDiscussions(self, message, title, username=None, userID=None):
        pass
    
    def createReplyMessageWalk(self, message, threadID, username=None, userID=None):
        # https://discbot.fandom.com/ru/wikia.php?controller=Fandom\MessageWall\MessageWall&method=createReply&format=json

        if not userID:
            userID = self.getUserID()

        payload = {
            'controller': 'Fandom\MessageWall\MessageWall',
            'method': 'createReply',
            'format': 'json'
        }

        body = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'wallOwnerId': str(userID),
            'threadId': str(threadID),
            'rawContent': message.getRawContent(),
            'jsonModel': message.getJSONModel(),
            'attachments': message.getAttachments()
        }

        response = self.__session.post(self.__apiSocialActivity, params=payload, data=body, headers=self.__headers)
        print('[{}] [{}] Отправили сообщение на стену обсуждения участника {} на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            userID,
            self.__apiSocialActivity
        ))
    
    def getWikiID(self):
        return self.__getWikiID
    
    def __getWikiID(self):
        payload = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'variables',
            'format': 'json'
        }

        response = self.__session.get(self.__apiRecentChanges, params=payload, headers=self.__headers)
        content = response.json()
        return content['query']['variables'][1]['*']
    
    def getUserID(self, username):
        message = self.getUserContributions(username=username, limit=1)
        return message[0]['userID']
    
    def getForumID(self, username=None, userID=None):
        message = self.getUserProfileActivity(username=username, userID=userID, limit=1)
        return message[0]['forumID']
    
    def __getToken(self):
        payload = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }

        response = self.__session.get(self.__apiRecentChanges, params=payload, headers=self.__headers)
        content = response.json()
        print(content)
        return content['query']['tokens']['csrftoken']

    def __getDateTimeNow(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
