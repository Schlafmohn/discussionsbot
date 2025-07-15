import json

import discbot
import discmess

from datetime import datetime, timezone, timedelta

class MyDiscussionsBot():
    def __init__(self):
        with open('configs/config.json', 'r') as file:
            config = json.loads(file.read())
        
        self.myBot = discbot.DiscussionsBot(
            config['username'],
            config['password'],
            config['wikilink']
        )

        self.fileSettings = 'configs/settings.json'
        with open(self.fileSettings, 'r') as file:
            self.settings = json.loads(file.read())

        # для успешной работы бота, сначала соберем все свежие правки и социальную активность на вики
        listNewMessages = self.myBot.getSocialActivity(self.settings['lastCheck'])

        for post in listNewMessages:
            # автоприветствие новых участников
            self.autogreeting(post)
            return
        
        self.updateSettings()
    
    def autogreeting(self, post):
        if post['userID'] in self.settings['famousUsers']:
            # если участник уже есть в кэше, его нет смысла проверять
            return
        
        if post['type'] in ['EDIT', 'NEW', 'LOG', 'CATEGORIZE']:
            dataPostsUser = self.myBot.getUserContributions(userID=post['userID'])
        else:
            dataPostsUser = self.myBot.getUserProfileActivity(userID=post['userID'])
        
        if (datetime.now(timezone.utc) - dataPostsUser[0]['timestamp']) <= timedelta(hours=24):
            # если участник присоединился к вики более, чем 24 часа, то его добавляют в кэш
            self.settings['famousUsers'].append(post['userID'])
            return
        
        # после всех проверок убеждаемся, что участник - новый, составляем приветственное сообщение и отправляем
        with open('configs/autogreeting.json', 'r') as file:
            dataAutogreeting = json.loads(file.read())

        postAutogreeting = discmess.DiscussionsMessage()
        for item in dataAutogreeting['jsonModel']['content']:
            if item['type'] == 'paragraph':
                postAutogreeting.addParagraph()
                self.helpCreatePostAutogreeting(post, postAutogreeting, item)
            
            if item['type'] == 'code_block':
                postAutogreeting.addCodeBlock()
            
            if item['type'] == 'bulletList':
                postAutogreeting.addBulletList().addListItem()
                self.helpCreatePostAutogreeting(post, postAutogreeting, item)
            
            if item['type'] == 'orderedList':
                postAutogreeting.addOrderedList().addListItem()
                self.helpCreatePostAutogreeting(post, postAutogreeting, item)

        self.myBot.createThreadMessageWalk(postAutogreeting, dataAutogreeting['title'], userID=post['userID'])
    
    def helpCreatePostAutogreeting(self, post, postAutogreeting, itemDataAutogreeting):
        for ktem in itemDataAutogreeting['content']:
            isMarkStrong = False
            isMarkItalic = False
            isMarkLink = None

            if '$USERNAME' in ktem['text']:
                ktem['text'] = ktem['text'].replace('$USERNAME', post['user'])
            
            if '$WIKINAME' in ktem['text']:
                ktem['text'] = ktem['text'].replace('$WIKINAME', self.myBot.getWikiName())
            
            if '$PAGENAME' in ktem['text']:
                # весь этот сложный цикл был сделан ради масштабируемости
                # конкретно - ради того, чтобы всегда была ссылка на вики-страницу
                self.helpCreatePostAutogreetingPagename(post, postAutogreeting, ktem)

                # ввиду того, что мы изменили само содержание `content`, то нижний код будет некорректно работать
                continue

            for mark in ktem.get('marks', []):
                if mark.get('type') == 'strong':
                    isMarkStrong = True
                        
                if mark.get('type') == 'em':
                    isMarkItalic = True
                        
                if mark.get('type') == 'link':
                    isMarkLink = mark['attrs']

            postAutogreeting.addText(ktem['text'],
                strong=isMarkStrong,
                italic=isMarkItalic,
                link=isMarkLink
            )
    
    def helpCreatePostAutogreetingPagename(self, post, postAutogreeting, ktemHelperAutogreeting):
        isMarkStrong = False
        isMarkItalic = False

        # разделяем строку на до и после - ссылка должна быть только на сам $PAGENAME
        ktemHelperAutogreeting['text'] = ktemHelperAutogreeting['text'].split('$PAGENAME')

        for mark in ktemHelperAutogreeting.get('marks', []):
            if mark.get('type') == 'strong':
                isMarkStrong = True
                        
            if mark.get('type') == 'em':
                isMarkItalic = True

        # сначала добавляем текст до $PAGENAME, сохраняя форматирование, заданное администраторами
        postAutogreeting.addText(ktemHelperAutogreeting['text'][0],
            strong=isMarkStrong,
            italic=isMarkItalic
        )

        # теперь добавляем само название $PAGENAME вместе с ссылкой, по прежнему сохраняя форматирование
        postAutogreeting.addText(post['thread'],
            strong=isMarkStrong,
            italic=isMarkItalic,
            link='https://discbot.fandom.com/ru/wiki/' + post['thread']
        )

        # ну и теперь добавляем текст после $PAGENAME, также сохраняя форматирование
        postAutogreeting.addText(ktemHelperAutogreeting['text'][1],
            strong=isMarkStrong,
            italic=isMarkItalic
        )
    
    def updateSettings(self):
        with open(self.fileSettings, 'w') as file:
            file.write(json.dumps(self.settings))

MyDiscussionsBot()
