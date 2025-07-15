import json
import requests

from datetime import datetime, timezone

class DiscussionsBot():
    def __init__(self, username, password, wikilink):
        self.__session = requests.Session()

        self.__headers = {
            'User-Agent': 'Discussions Bot v0.1 14 July, 2025',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest'
        }

        self.__login(username, password) # заходим в аккаунт участника-бота
        self.__getMetaInfo(wikilink) # получаем метаданные о себе и о вики, на которой будем работать

        self.__linkAPI_PHP = self.__wikilink + '/api.php'
        self.__linkWikiaAPI_PHP = self.__wikilink + '/wikia.php'
    
    def __login(self, username, password):
        url = 'https://services.fandom.com/mobile-fandom-app/fandom-auth/login'

        data = {
            'username': username,
            'password': password
        }

        response = self.__session.post(url, data=data, headers=self.__headers)

        print('[{}] [{}] Вошли в аккаунт участника-бота (ID {}) на Фэндоме'.format(
            self.__getDateTimeNow(),
            response.status_code,
            response.json()['user_id']
        ))
    
    def __getMetaInfo(self, wikilink):
        ''' для корректной работы бота обсуждений нужны следующие данные:
            - верное название участника-бота (непонятно, что в config.json находится)
            - ID участника-бота
            - верно название вики
            - язык вики (русский, английский, польский)
            - и верный URL вики (да, я настолько даже себе не доверяю) '''

        payload = {
            'action': 'query',
            'meta': 'userinfo|siteinfo',
            'siprop': 'general|variables',
            'format': 'json'
        }

        response = self.__session.get(wikilink + 'api.php', params=payload, headers=self.__headers)
        content = response.json()

        # данные для участника-бота находятся в `userinfo`
        self.__botUsername = content['query']['userinfo']['name']
        self.__botUserID = content['query']['userinfo']['id']

        # данные для вики находятся в `sitename`
        self.__wikiname = content['query']['general']['sitename']
        self.__wikilang = content['query']['general']['lang']
        self.__wikilink = content['query']['general']['server'] + content['query']['general']['scriptpath']

        # а вот с ID вики намного сложнее, оно находится в `wgCityId`
        self.__wikiID = content['query']['variables'][1]['*']

        print('[{}] [{}] Получили метаданные участника-бота (ID {}) и вики на Фэндоме (ID {})'.format(
            self.__getDateTimeNow(),
            response.status_code,
            content['query']['userinfo']['id'],
            content['query']['variables'][1]['*']
        ))
    
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
            'rcprop': 'user|userid|comment|timestamp|title|ids|size',
            'rcshow': '!anon|!bot', # игнорируем любые правки от анонимных участников и от других ботов
            'rclimit': str(limit),
            'format': 'json'
        }

        response = self.__session.get(self.__linkAPI_PHP, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили свежие правки на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            self.__linkAPI_PHP
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

        response = self.__session.get(self.__linkWikiaAPI_PHP, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили социальную активность на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            self.__linkWikiaAPI_PHP
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

        response = self.__session.get(self.__linkAPI_PHP, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили вклад участника {} на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            telnetUser,
            self.__linkAPI_PHP
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

        response = self.__session.get(self.__linkWikiaAPI_PHP, params=payload, headers=self.__headers)
        print('[{}] [{}] Получили активность участника {} на вики {}'.format(
            self.__getDateTimeNow(),
            response.status_code,
            userID,
            self.__linkWikiaAPI_PHP
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
                'forumID': i['ns'],

                # добавлено для совместимости с `helpSocialActivity()`
                'position': i['revid'],
                'content': i['comment'],

                'jsonModel': i['comment'],
                'attachments': i['size']
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
            if i['createdBy']['id'] == '0' or i['createdBy']['id'] == str(self.__botUserID):
                continue

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
                'forumID': int(i['forumId']),

                'position': i['position'],
                'content': i['rawContent'],

                'jsonModel': i['jsonModel'],
                'attachments': i['_embedded']['attachments']
            })

            # на форуме пользователи могут пинговать участников в буквальном смысле, поэтому проверяем наличие ID бота в `atMentions`
            if not i['_embedded']['attachments'][0]['atMentions']:
                messages[-1]['pingDiscBot'] = False
            elif i['_embedded']['attachments'][0]['atMentions'] == str(self.__botUserID):
                messages[-1]['pingDiscBot'] = True
            
            # но вот на стене обсуждения пользователи не могут пинговать, поэтому стоит проверить, чтобы стена обсуждения принадлежала боту
            if i['forumName'] == '{} Message Wall'.format(self.__botUsername):
                messages[-1]['pingDiscBot'] = True
        
        messages.reverse() # список выводится от старых к новым сообщениям и комментариям
        
        return messages
    
    def createThreadDiscussions(self, discMessage, title, forumID):
        queryStringParameters = {
            'controller': 'DiscussionThread',
            'method': 'create'
            'forumId': str(forumID)
        }

        requestData = {
            'MIME Type': 'application/json',
            'Encoding': 'utf-8',
            'Request Data': {
                'body': discMessage.getRawContent(),
                'jsonModel': discMessage.getJSONModel(),
                'attachments': discMessage.getAttachments(),
                'forumId': str(forumID),
                'siteId': str(self.__wikiID),
                'title': title,
                'source': 'DESKTOP_WEB_FEPO',
                'funnel': 'TEXT',
                'articleIds': []
            }
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Create the new thread on Discussions'.format(self.__getDateTimeNow(), response.status_code))
    
    def createThreadMessageWall(self, discMessage, title, username=None, userID=None):
        if not userID:
            userID = self.getUserID(username)

        queryStringParameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'createThread',
            'format': 'json'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'wallOwnerId': str(userID),
            'title': title,
            'rawContent': discMessage.getRawContent(),
            'jsonModel': discMessage.getJSONModel(),
            'attachments': discMessage.getAttachments()
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Create the new thread on Message Wall'.format(self.__getDateTimeNow(), response.status_code))
    
    def createThreadArticleComments(self, discMessage, pagename):
        queryStringParameters = {
            'controller': 'ArticleCommentsController',
            'method': 'postNewCommentThread'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'title': pagename,
            'namespace': '0',
            'token': self.__getToken(),
            'jsonModel': discMessage.getJSONModel(),
            'attachments': discMessage.getAttachments()
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Create the new thread on Article Comments'. format(self.__getDateTimeNow(), response.status_code))
    
    def createReplyDiscussions(self, discMessage, threadID):
        queryStringParameters = {
            'controller': 'DiscussionPost',
            'method': 'create'
        }

        requestData = {
            'MIME Type': 'application/json',
            'Encoding': 'utf-8',
            'Request Data': {
                'body': discMessage.getRawContent(),
                'jsonModel': discMessage.getJSONModel(),
                'attachments': discMessage.getAttachments(),
                'siteId': str(self.__wikiID),
                'source': 'DESKTOP_WEB_FEPO',
                'threadId': str(threadID)
            }
        }
        
        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Create the reply on Discussions'. format(self.__getDateTimeNow(), response.status_code))
    
    def createReplyMessageWall(self, discMessage, threadID, username=None, userID=None):
        if not userID:
            userID = self.getUserID(username)

        queryStringParameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'createReply',
            'format': 'json'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'wallOwnerId': str(userID),
            'threadId': str(threadID),
            'rawContent': discMessage.getRawContent(),
            'jsonModel': discMessage.getJSONModel(),
            'attachments': discMessage.getAttachments()
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Create the reply on Message Wall'.format(self.__getDateTimeNow(), response.status_code))
    
    def createReplyArticleComments(self, discMessage, threadID, pagename):
        queryStringParameters = {
            'controller': 'ArticleCommentsController',
            'method': 'postNewCommentReply'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'threadId': str(threadID),
            'title': pagename,
            'namespace': '0',
            'token': self.__getToken(),
            'jsonModel': discMessage.getJSONModel(),
            'attachments': discMessage.getAttachments()
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Create the reply on Article Comments'.format(self.__getDateTimeNow(), response.status_code))
    
    def deletePostDiscussions(self, threadID=None, postID=None):
        queryStringParameters = {
            'controller': 'DiscussionThread',
            'method': 'delete'
        }

        if threadID:
            payload['threadId'] = str(threadID)
        else:
            payload['postId'] = str(postID)
        
        requestData = {
            'MIME Type': 'multipart/form-data',
            'Boundary': '----WebKitFormBoundaryep0uj55I2xhFAxby',
            'Request Data': '------WebKitFormBoundaryep0uj55I2xhFAxby\nContent-Disposition: form-data; name="suppressContent"\n\nfalse\n------WebKitFormBoundaryep0uj55I2xhFAxby--'
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Delete the thread or the post on Discussions'. format(self.__getDateTimeNow(), response.status_code))
    
    def deletePostMessageWall(self, threadID=None, postID=None, username=None, userID=None):
        if not userID:
            userID = self.getUserID(username)

        queryStringParameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'format': 'json'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'wallOwnerId': str(userID),
            'suppressContent': 'false'
        }

        if threadID:
            payload['method'] = 'delete',
            body['postId'] = str(threadID)
        else:
            payload['method'] = 'deleteReply',
            body['postId'] = str(postID)

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Delete the thread or the post on Message Wall'. format(self.__getDateTimeNow(), response.status_code))
    
    def deletePostArticleComments(self, postID, pagename):
        queryStringParameters = {
            'controller': 'ArticleCommentsController',
            'method': 'deletePost'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'postId': str(postID),
            'token': self.__getToken(),
            'suppressContent': 'false',
            'title': pagename,
            'namespace': '0'
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=payload, data=body, headers=self.__headers)
        print('[{}] [{}] Delete the thread or the post on Article Comments'. format(self.__getDateTimeNow(), response.status_code))
    
    def reportPostDiscussions(self, postID):
        queryStringParameters = {
            'controller': 'DiscussionModeration',
            'method': 'reportPost',
            'postId': str(postID)
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, headers=self.__headers)
        print('[{}] [{}] Report the thread or the post on Discussions'. format(self.__getDateTimeNow(), response.status_code))
    
    def reportPostMessageWall(self, postID):
        queryStringParameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'reportPost',
            'format': 'json'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'postId': str(postID)
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Report the thread or the post on Message Wall'. format(self.__getDateTimeNow(), response.status_code))
    
    def reportPostArticleComments(self, postID, pagename):
        queryStringParameters = {
            'controller': 'ArticleCommentsController',
            'method': 'reportPost'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'postId': str(postID),
            'title': pagename,
            'namespace': '0',
            'token': self.__getToken()
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Report the thread or the post on Article Comments'. format(self.__getDateTimeNow(), response.status_code))
    
    def lockPostDiscussions(self, threadID):
        queryStringParameters = {
            'controller': 'DiscussionModeration',
            'method': 'lock',
            'threadId': str(postID)
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, headers=self.__headers)
        print('[{}] [{}] Lock the thread on Discussions'. format(self.__getDateTimeNow(), response.status_code))
    
    def lockPostMessageWall(self, threadID, username=None, userID=None):
        if not userID:
            userID = self.getUserID(username)

        queryStringParameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'lockThread',
            'format': 'json'
        }

        requestData = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self.__getToken(),
            'wallOwnerId': str(userID),
            'threadId': str(threadID)
        }

        response = self.__session.post(self.__linkWikiaAPI_PHP, params=queryStringParameters, data=requestData, headers=self.__headers)
        print('[{}] [{}] Lock the thread on Message Wall'.format(self.__getDateTimeNow(), response.status_code))
    
    # начало служебных геттеров для получения закрытых полей
    def getBotUserName(self):
        return self.__botUsername

    def getBotUserID(self):
        return self.__botUserID

    def getWikiName(self):
        return self.__wikiname

    def getWikiLang(self):
        return self.__wikilang

    def getWikiLink(self):
        return self.__wikilink

    def getWikiID(self):
        return self.__wikiID
    # конец закрытых служебных полей
    
    def getUserID(self, username):
        message = self.getUserContributions(username=username, limit=1)
        return message[0]['userID']
    
    def getForumID(self, username=None, userID=None):
        message = self.getUserProfileActivity(username=username, userID=userID, limit=1)
        return message[0]['forumID']
    
    def getPageName(self, message):
        if not message['type'] == 'ARTICLE_COMMENT':
            return message['thread']
        
        return self.__getArticleTitle(message['forumID'])
    
    def getPageLink(self, message):
        if message['type'] in ['EDIT', 'NEW', 'LOG', 'CATEGORIZE']:
            # если `type` сообщения входит в категорию обычного вики-пространства, то имя страницы хранится в `thread`
            return self.__wikilink + '/wiki/' + message['thread']
        
        if message['type'] == 'FORUM':
            # если `type` равен `FORUM`, то полная ссылка строится вот так:
            return self.__wikilink + '/f/p/' + str(message['threadID']) + '/r/' + str(message['postID'])
        
        if message['type'] == 'WALL':
            # если работаем со стеной обсуждения, то сначала нужно вытащить имя, чья эта стена обсуждения вообще
            # в начале `forum` находится имя владельца, а потом всегда идет стандартная фраза ` Message Wall` (13 символов)
            return self.__wikilink + '/wiki/Message_Wall:' + message['forum'][:-13] + '?threadId=' + str(message['threadID']) + '#' + str(message['postID'])

        if message['type'] == 'ARTICLE_COMMENT':
            return self.__wikilink + '/wiki/' + self.getArticleTitle(message['forumID']) + '?commentId=' + str(message['threadID']) + '&replyId=' + str(message['postID'])
    
    def __getArticleTitle(self, forumID):
        payload = {
            'controller': 'ArticleComments',
            'method': 'getArticleTitle',
            'stablePageId': str(forumID),
            'format': 'json'
        }

        response = self.__session.get(self.__linkWikiaAPI_PHP, params=payload, headers=self.__headers)
        content = response.json()
        return content['title']
    
    def __getToken(self):
        payload = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }

        response = self.__session.get(self.__linkAPI_PHP, params=payload, headers=self.__headers)
        content = response.json()
        return content['query']['tokens']['csrftoken']

    def __getDateTimeNow(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
