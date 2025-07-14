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
       messages = discbot.DiscussionsBot.getWikiActivity(self.myBot, self.settings['lastCheck'])

       for post in messages:
            # автоприветствие новых участников
           self.autogreeting(post)
        
        self.updateSettings()
    
    def autogreeting(self, mess):
        if mess['userID'] in self.settings['famousUsers']:
            # если участник уже есть в кэше, его нет смысла проверять
            return
        
        if mess['type'] in ['EDIT', 'NEW', 'LOG', 'CATEGORIZE']:
            dataUser = discbot.DiscussionsBot.getUserContributions(self.myBot, userID=mess['userID'])
        else:
            dataUser = discbot.DiscussionsBot.getUserProfileActivity(self.myBot, userID=mess['userID'])
        
        if (datetime.now(timezone.utc) - dataUser[0]['timestamp']) <= timedelta(hours=24):
            # если участник присоединился к вики более, чем 24 часа, то его добавляют в кэш
            self.settings['famousUsers'].append(mess['userID'])
            return
        
        with open('configs/autogreeting.json', 'r') as file:
            fileAutogreeting = json.loads(file.read())
        
        messAutogreeting = discmess.DiscussionsMessage()
        for item in fileAutogreeting['jsonModel']['content']:
            if item['type'] == 'paragraph':
                messAutogreeting.addParagraph()
            
            elif item['type'] == 'code_block':
                messAutogreeting.addCodeBlock()
            
            elif item['type'] == 'bulletList':
                messAutogreeting.addBulletList()
            
            elif item['type'] == 'orderedList':
                messAutogreeting.addOrderedList()
            
            for ktem in item['content']:
                
    
    def updateSettings(self):
        with open(self.fileSettings, 'w') as file:
            file.write(json.dumps(self.settings))

MyDiscussionsBot()
