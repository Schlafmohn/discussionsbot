import json

import autogreeting

from gendiscbot import discmess

def commands(self, post):
    if not post['pingDiscBot']:
        return
    
    with open('languages/{}.json'.format(self.myBot.getWikiLang()), 'r') as file:
        dataReplyPost = json.loads(file.read())
    
    if 'ping' in post['content'].lower():
        replyPostCommand = discmess.DiscussionsMessage()
        
        replyPostCommand.addText(post['user'], strong=True).addText(', привет! Я, ').addText(self.myBot.getBotUserName(), strong=True)
        replyPostCommand.addText(', – бот обсуждений, написанный абсолютно с нуля участником Зубенко Михаил Петрович. Если у тебя будут какие-то вопросы, лучше обращайся к нему. Держи даже ')
        replyPostCommand.addText('ссылку', link='https://warriors-cats.fandom.com/ru/wiki/Стена_обсуждения:Зубенко_Михаил_Петрович').addText('. Мне нет никакого смысла писать, я не обладаю даже встроенной функцией от Chat GPT 🏓')

        self.myBot.createReplyMessageWall(
            replyPostCommand,
            threadID=post['threadID'],
            userID=self.myBot.getBotUserID()
        )

        return
    
    if 'update autotitle' in post['content'].lower():
        # обновление заголовка приветствия новых участников

        newTitle = post['content'].split('update autotitle ')[1]

        with open('configs/autogreeting.json', 'r') as file:
            dataAutogreeting = json.loads(file.read())
        
        with open('configs/autogreeting.json', 'w') as file:
            dataAutogreeting['title'] = newTitle
            file.write(json.dumps(dataAutogreeting))

        replyPostCommand = discmess.DiscussionsMessage()
        replyPostCommand.addText(dataReplyPost['UPDATE AUTOTITLE'].replace('$USERNAME', post['user']).replace('$TITLE', newTitle))

        self.myBot.createReplyMessageWall(
            replyPostCommand,
            threadID=post['threadID'],
            userID=self.myBot.getBotUserID()
        )

        return
    
    if 'update autopost' in post['content'].lower():
        # обновление всего сообщения приветствия новых участников

        with open('configs/autogreeting.json', 'r') as file:
            dataAutogreeting = json.loads(file.read())

        with open('configs/autogreeting.json', 'w') as file:
            # нужно подправить `jsonModel`, потому что в нем первый `paragraph` относится к команде `update autopost`
            jsonModel = json.loads(post['jsonModel'])
            jsonModel['content'].pop(0)

            dataAutogreeting['rawContent'] = post['content'].split('update autopost ')[1]
            dataAutogreeting['jsonModel'] = jsonModel
            dataAutogreeting['attachments'] = post['attachments']

            print(dataAutogreeting, '\n\n\n', dataAutogreeting['jsonModel'])

            file.write(json.dumps(dataAutogreeting))
        
        replyPostCommand = discmess.DiscussionsMessage()
        replyPostCommand.addText(dataReplyPost['UPDATE AUTOPOST'].replace('$USERNAME', post['user']))

        self.myBot.createReplyMessageWall(
            replyPostCommand,
            threadID=post['threadID'],
            userID=self.myBot.getBotUserID()
        )

        return
