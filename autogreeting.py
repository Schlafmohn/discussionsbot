import json
import time

from datetime import datetime
from datetime import timezone
from datetime import timedelta

class Autogreeting:
    def isUserNewOnWikiAndDiscussions(self, userID, nowTime):
        ''' проверяет: новый ли участник на вики и в обсуждениях или нет? возвращается либо True (новый), либо False (неновый) '''

        if self.isUserNewOnWiki(userID, nowTime):
            return self.isUserNewOnDiscussions(userID, nowTime)

        return False

    def isUserNewOnWiki(self, userID, nowTime):
        ''' проверяет: новый ли участник на вики или нет? возвращает либо True (новый), либо False (неновый) '''

        firstContr = self.getFirstUserContributions(userID)
        time.sleep(3)

        print('Проверка этого участника на вики!')
        if firstContr:
            thenTime = datetime.strptime(firstContr['timestamp'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            print('Check:', nowTime - thenTime)

            if (nowTime - thenTime) < timedelta(minutes=30):
                # если разница между нынешним временем и временем первой правки меньше 30 минут, значит, он – новичок
                return True
            else:
                return False

        return True

    def isUserNewOnDiscussions(self, userID, nowTime):
        ''' проверяет: новый ли участник в обсуждениях или нет? возвращает либо True (новый), либо False (неновый) '''

        # в API Discussions почему-то используется UNIX-время, поэтому нам его нужно перевести в datetime по UTC
        firstPost = self.getFirstUserProfileActivity(userID)
        time.sleep(3)

        print('Проверка этого участника в обсуждениях!')
        if firstPost:
            thenTime = datetime.fromtimestamp(firstPost['creationDate']['epochSecond'], timezone.utc)
            print('Check:', nowTime - thenTime)

            if (nowTime - thenTime) < timedelta(minutes=30):
                # если разница между нынешним временем и временем первой правки меньше 30 минут, значит, он – новичок
                return True
            else:
                return False

        return True

    def autogreeting(self, someEdit):
        with open('autogreeting.json', 'r') as file:
            textAutogreeting = json.loads(file.read())

        with open('languages/lang{}.json'.format(self.wikilang), 'r') as file: # в будущем планируется многоязычность бота, как было у чат-бота Bottovodstvo
            language = json.loads(file.read())

        # здесь и далее с jsonModel обращаются как со строкой — ошибок здесь нет, она действительно строка

        # добавляем имя нового участника
        textAutogreeting['body'] = textAutogreeting['body'].replace('{{username}}', someEdit['username'])
        textAutogreeting['jsonModel'] = textAutogreeting['jsonModel'].replace('{{username}}', someEdit['username'])

        # добавляем заголовок статьи, где была сделана первая правка участником
        textAutogreeting['body'] = textAutogreeting['body'].replace('{{threadtitle}}', someEdit['title']).replace('{{pagetitle}}', someEdit['title'])
        textAutogreeting['jsonModel'] = textAutogreeting['jsonModel'].replace('{{threadtitle}}', someEdit['title']).replace('{{pagetitle}}', someEdit['title'])

        # todo: переписать к 8 сентябрю
        textAutogreeting['body'] = textAutogreeting['body'].replace('{{postlink}}', someEdit['href'])
        textAutogreeting['jsonModel'] = textAutogreeting['jsonModel'].replace('{{postlink}}', someEdit['href'])

        # добавляем слова «статья/тема» и «правка/сообщение/комментарий» в нужном падеже через цикл (раньше было хуже)
        for ikj in language['containerType'][someEdit['containerType']]:
            textAutogreeting['body'] = textAutogreeting['body'].replace(ikj, language['containerType'][someEdit['containerType']][ikj])
            textAutogreeting['jsonModel'] = textAutogreeting['jsonModel'].replace(ikj, language['containerType'][someEdit['containerType']][ikj])

        body = {
            'body': textAutogreeting['body'],
            'jsonModel': textAutogreeting['jsonModel'],
            'attachments': textAutogreeting['attachments']
        }

        # добавляем текст приветственного сообщения из autogreeting.json с сохранением форматирования
        newMessage = message.Message(self, body)
        newMessage.createThreadMessageWall(username, userID, textAutogreeting['title']) # в будущем заголовок темы можно будет настраивать, пока так
        time.sleep(3) # чтобы не перегружать сервера Фэндома

    def autogreetingSettings(self, subCommand, someEdit):
        if not 'sysop' in someEdit['badgePermission']:
            return

        if subCommand == 'on' or subCommand == 'yes':
            self.wikiSettings['autogreeting'] = True
            textMessage = self.getTextMessage('autogreeting on')

        elif subCommand == 'off' or subCommand == 'no':
            self.wikiSettings['autogreeting'] = False
            textMessage = self.getTextMessage('autogreeting off')

        elif subCommand == 'new' or subCommand == 'update':
            pass

        elif subCommand == 'title':
            textMessage = self.getTextMessage('autogreeting new title')

        # добавляем имя участника
        textMessage['body'] = textMessage['body'].replace('{{username}}', someEdit['username'])
        textMessage['jsonModel'] = textMessage['jsonModel'].replace('{{username}}', someEdit['username'])

        body = {
            'body': textMessage['body'],
            'jsonModel': textMessage['jsonModel'],
            'attachments': textMessage['attachments']
        }

        # добавляем текст приветственного сообщения из textMessage.json с сохранением форматирования
        newMessage = message.Message(self, body)
        newMessage.createReplyMessageWall(someEdit['username'], someEdit['userID'], someEdit['threadID'])
        time.sleep(3) # чтобы не перегружать сервера Фэндома
