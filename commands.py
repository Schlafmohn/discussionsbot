import time
import json

import message
import autogreeting

class CommandsMyBot(autogreeting.Autogreeting):
    def getTextMessage(self, command):
        with open('textMessage.json', 'r') as file:
            textMessage = json.loads(file.read())

        return textMessage[command]

    def help(self, someEdit):
        textMessage = self.getTextMessage('help')

        # добавляем имя участника
        textMessage['body'] = textMessage['body'].replace('{{username}}', someEdit['username'])
        textMessage['jsonModel'] = textMessage['jsonModel'].replace('{{username}}', someEdit['username'])

        body = {
            'body': textMessage['body'],
            'jsonModel': textMessage['jsonModel'],
            'attachments': textMessage['attachments']
        }

        # добавляем текст сообщения-помощи из textMessage.json с сохранением форматирования
        newMessage = message.Message(self, body)

        if someEdit['containerType'] == 'FORUM':
            pass
        elif someEdit['containerType'] == 'WALL':
            newMessage.createReplyMessageWall(someEdit['username'], someEdit['userID'], someEdit['threadID'])
        elif someEdit['containerType'] == 'ARTICLE_COMMENT':
            pass
        
        time.sleep(3) # чтобы не перегружать сервера Фэндома
