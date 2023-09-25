import json
import requests

# todo: сделать метод addMention() совместимым с addListItem()
# todo: обязательно сравнить и проверить отправление файлов бота от обычного участника

class Message:
    def __init__(self, DiscussionsBot):
        ''' для создания сообщения с нуля '''

        body = {
            'body': '',
            'jsonModel': json.dumps({ 'type': 'doc', 'content': [] }),
            'attachments': {
                'contentImages': [],
                'openGraphs': [],
                'atMentions': []
            }
        }

        self.__init__(DiscussionsBot, body)

    def __init__(self, DiscussionsBot, body):
        ''' для создания сообщения, у которого уже есть содержимое '''

        self.__DiscussionsBot = DiscussionsBot

        # можно было бы написать и self.__body = body, но желательно проверить, чтобы каждый элемент присутствовал
        # если какой-то элемент будет отсутствовать, значит, сообщение изначально было неверно составлено и вылетит ошибка
        self.__body = {
            'body': body.get('body'), # этот ключ на MessageWall называется rawContent
            'jsonModel': json.loads(body['jsonModel']), # здесь добавляется содержимое сообщения
            'attachments': {
                'contentImages': body['attachments']['contentImages'],
                'openGraphs': body['attachments']['openGraphs'],
                'atMentions': body['attachments']['atMentions']
            }
        }

        if not self.__body['body']:
            self.__body['body'] = body['rawContent']

    def __str__(self):
        return str(self.__body)

    def __add__(self, other):
        if not self.__DiscussionsBot == other.__DiscussionsBot:
            print('Нельзя сложить два сообщения от двух разных ботов!')
            return

        body = {
            'body': self.__body['body'] + other.__body['body'],
            'jsonModel': {
                'type': 'doc',
                'content': self.__body['jsonModel']['content'] + other.__body['jsonModel']['content']
            },
            'attachments': {
                'contentImages': self.__body['attachments']['contentImages'] + other.__body['attachments']['contentImages'],
                'openGraphs': self.__body['attachments']['openGraphs'] + other.__body['attachments']['openGraphs'],
                'atMentions': self.__body['attachments']['atMentions'] + other.__body['attachments']['atMentions']
            }
        }

        return Message(self.__DiscussionsBot, body)

    def __addingText(self, text, strong, em, href=None, title=None, userID=None):
        ''' форматирует участок сообщения: полужирный, курсив, ссылка и уведомление '''

        adding = {
            'type': 'text',
            'marks': [],
            'text': text
        }

        if strong:
            adding['marks'].append({ 'type': 'strong' })
        if em:
            adding['marks'].append({ 'type': 'em' })
        if href:
            adding['marks'].append({ 'type': 'link' })
            adding['marks'][-1]['attrs'] = { 'href': href, 'title': title }
            # title будет сделано во второй версии бота, сначала None
        if mention:
            adding['marks'].append({ 'type': 'mention' })
            adding['marks'][-1]['attrs'] = { 'href': None, 'userId': str(userID), 'username': text[1:] }
            # важно: после ноябрьского обновления 'userId' стало строкой

        return adding

    def addMention(self, username, userID):
        ''' добавляет оповещение и уведомление участнику на Фэндоме '''
        # обычные участники не могут оповещение выделять полужирным или курсивным шрифтом, поэтому их нет в методе

        text = '@' + username
        self.__body['body'] += text
        adding = self.__addingText(text, False, False, userID=userID)
        self.__body['jsonModel']['content'][-1]['content'].append(adding)
        self.__body['attachments']['atMentions'].append({ 'id': str(userID) }) # без этого у участника не появится уведомление

    def newParagraph(self):
        ''' создает новый абзац (параграф) в сообщении '''

        if self.__body['body'] and self.__body['body'][-1] != '\n':
            self.__body['body'] += '\n'

        adding = {
            'type': 'paragraph',
            'content': [] # здесь добавляется содержимое абзаца (параграфа)
        }

        if self.__body['jsonModel']['content'][-1] == adding:
            # почему-то, чтобы создать два пустых абзаца, нужно обязательно избавляться от 'content' в ['jsonModel']['content']
            self.__body['jsonModel']['content'][-1].pop('content')

        self.__body['jsonModel']['content'].append(adding)

    def addText(self, text, strong=False, em=False, href=None, title=None, newParagraph=False):
        ''' добавляет текст в сообщение '''

        if newParagraph:
            # создание абзаца (параграфа) обязательно перед вводом текста
            self.newParagraph()

        self.__body['body'] += text
        adding = self.__addingText(text, strong, em, href, title)
        self.__body['jsonModel']['content'][-1]['content'].append(adding)

    def addStrongText(self, text, href=None, title=None, newParagraph=False):
        ''' добавляет полужирный текст в сообщение '''

        self.addText(text, strong=True, href=href, title=title, newParagraph=newParagraph)

    def addEmText(self, text, href=None, title=None, newParagraph=False):
        ''' добавляет курсивный текст в сообщение '''

        self.addText(text, em=True, href=href, title=title, newParagraph=newParagraph)

    def addStrongEmText(self, text, href=None, title=None, newParagraph=False):
        ''' добавляет полужирный и курсивный текст в сообщение '''

        self.addText(text, strong=True, em=True, href=href, title=title, newParagraph=newParagraph)

    def newList(self, type):
        ''' создает новый список в сообщении '''
        # type='bulletList' создает маркированный список
        # type='orderedList' создает нумерованный список

        adding = {
            'type': type,
            'attrs': { 'createdWith': None },
            'content': [] # здесь добавляется содержимое списка
        }

        self.__body['jsonModel']['content'].append(adding)

    def newListItem(self):
        ''' создает новый пункт в списке сообщения '''

        self.__body['body'] += '\n'

        adding = {
            'type': 'listItem',
            'content': [{
                'type': 'paragraph',
                'content': [] # здесь добавляется содержимое пункта в списке
            }]
        }

        self.__body['jsonModel']['content'][-1]['content'].append(adding)

    def addListItem(self, text, marks=[], href=None, title=None, newListItem=False):
        ''' добавляет текст в пункт списка в сообщении '''

        if newListItem:
            # создание пункта в список обязательно перед вводом текста
            self.newListItem()

        self.__body['body'] += text
        adding = self.__addingText(text, marks, href, title)
        self.__body['jsonModel']['content'][-1]['content'][-1]['content'][-1]['content'].append(adding)

    def newCodeBlock(self, text):
        ''' форматирует участок сообщения: без форматирования '''

        self.addCodeBlock(text)

    def addCodeBlock(self, text):
        self.__body['body'] += text

        adding = {
            'type': 'code_block',
            'content': [{
                'type': 'text',
                'text': text
            }]
        }

        self.__body['jsonModel']['content'].append(adding)

    def createThreadDiscussion(self, title, funnel='TEXT', forumId=None, articleNames=[], source='DESKTOP_WEB_FEPO'):
        ''' создает новый топик в обсуждениях '''

        # source необязательный атрибут для отправления сообщения, видимо, его используют для статистики
        # source='DESKTOP_WEB_FEPO' сообщение отправлено с компьютерного браузера
        # source='UNCATEGORIZED' сообщение отправлено с неизвестного устройства

        # funnel='TEXT' создает текстовое сообщение
        # funnel='POLL' создает сообщение с опросом

        if not forumId:
            # категория General имеет идентичный ID с вики
            forumId = self.__DiscussionsBot.wikiID

        body = self.__body.copy()
        body['forumId'] = str(forumId)
        body['siteId'] = str(self.__DiscussionsBot.wikiID)
        body['title'] = title
        body['source'] = source
        body['funnel'] = funnel # 'POLL' будет сделано во второй версии бота, сначала 'TEXT'
        body['articleIds'] = []

        if articleNames:
            body['articleIds'] = self.__getPagesIDs(articleNames)

        body['body'] = title + ' ' + body['body'] # точьно ??

        body['jsonModel'] = json.dumps(body['jsonModel'])
        body = json.dumps(body)

        payload = {
            'controller': 'DiscussionThread',
            'method': 'create',
            'forumId': str(forumId)
        }

        response = self.__DiscussionsBot.session.post(self.__DiscussionsBot.wikiPHP, params=payload, data=body, headers=self.__DiscussionsBot.headers)
        print('Отправка сообщения:', response)

    def createPostDiscussion(self, threadId, source='DESKTOP_WEB_FEPO'):
        ''' отправляет сообщение в существующий топик обсуждениях '''

        body = self.__body.copy()
        body['siteId'] = str(self.__DiscussionsBot.wikiID) # после ноябрьского обновления это строка
        body['source'] = source
        body['threadId'] = str(threadId) # после ноябрьского обновления это строка

        body['jsonModel'] = json.dumps(body['jsonModel'])
        body = json.dumps(body)

        payload = {
            'controller': 'DiscussionPost',
            'method': 'create'
        }

        response = self.__DiscussionsBot.session.post(self.__DiscussionsBot.wikiPHP, params=payload, data=body, headers=self.__DiscussionsBot.headers)
        print('Отправка сообщения:', response)

    def createThreadMessageWall(self, username, userID, title):
        ''' создает новый топик на стене обсуждения участника '''

        body = self.__body.copy()
        body['token'] = self.__getEditToken()
        body['wallOwnerId'] = str(userID)
        body['title'] = title
        body['rawContent'] = body.pop('body')

        body['jsonModel'] = json.dumps(body['jsonModel'])
        body['attachments'] = json.dumps(body['attachments'])

        payload = {
            'controller': 'Fandom\MessageWall\MessageWall',
            'method': 'createThread',
            'format': 'json' # нужен ли он здесь ?
        }

        response = self.__DiscussionsBot.session.post(self.__DiscussionsBot.wikiPHP, params=payload, data=body, headers=self.__DiscussionsBot.headers)
        print('Отправка сообщения:', response)

    def createReplyMessageWall(self, username, userID, threadId):
        ''' отправляет сообщение в существующий топик на стене обсуждения участника '''

        # https://bot-obsuzhdeniya.fandom.com/ru/wikia.php?controller=Fandom%5CMessageWall%5CMessageWall&method=createReply&format=json

        body = self.__body.copy()
        body['token'] = self.__getEditToken()
        body['wallOwnerId'] = str(userID)
        body['threadId'] = str(threadId)
        body['rawContent'] = body.pop('body')

        body['jsonModel'] = json.dumps(body['jsonModel'])
        body['attachments'] = json.dumps(body['attachments'])

        payload = {
            'controller': 'Fandom\MessageWall\MessageWall',
            'method': 'createReply',
            'format': 'json' # нужен ли он здесь ?
        }

        response = self.__DiscussionsBot.session.post(self.__DiscussionsBot.wikiPHP, params=payload, data=body, headers=self.__DiscussionsBot.headers)
        print('Отправка сообщения:', response)
        print(response)

    def __getUserID(self, username):
        payload = {
            'action': 'query',
            'list': 'users',
            'ususers': username,
            'format': 'json'
        }

        response = self.__DiscussionsBot.session.get(self.__DiscussionsBot.wikiAPI, params=payload, headers=self.__DiscussionsBot.headers)
        content = response.json()
        userID = content['query']['users'][0]['userid']
        return userID

    def __getEditToken(self):
        payload = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }

        response = self.__DiscussionsBot.session.get(self.__DiscussionsBot.wikiAPI, params=payload, headers=self.__DiscussionsBot.headers)
        content = response.json()
        editToken = content['query']['tokens']['csrftoken']
        return editToken

    def __getPagesIDs(self, pages):
        titles = ''
        for i in pages:
            titles += i + '|'

        payload = {
            'action': 'query',
            'meta': 'info',
            'titles': titles[:-1],
            'format': 'json'
        }

        response = self.__DiscussionsBot.session.get(self.__DiscussionsBot.wikiAPI, params=payload, headers=self.__DiscussionsBot.headers)
        content = response.json()

        pagesIDs = []
        for i in content['query']['pages']:
            pagesIDs.append(str(content['query']['pages'][i]['pageid']))

        return pagesIDs

if __name__ == '__main__':
    pass
