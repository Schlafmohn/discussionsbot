import json
import time

import commands
import autogreeting

from gendiscbot import discbot
from gendiscbot import discmess

from datetime import datetime

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
        
        while True:
            # для успешной работы бота, сначала соберем все свежие правки и социальную активность на вики
            listNewMessages = self.myBot.getSocialActivity(self.settings['lastCheck'])

            self.workMyBot(listNewMessages)
            self.settings['lastCheck'] = listNewMessages[-1]['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
            self.updateSettings()
            
            time.sleep(60 * 5) # каждые 5 минут бот будет подхватывать новые данные с вики
    
    def workMyBot(self, listNewMessages):
        for post in listNewMessages:
            # time.sleep(60) # Фэндом жалуется, если слишком часто дергать его сервера
            # autogreeting.autogreeting(self, post) # автоприветствие новых участников

            # time.sleep(60)
            commands.commands(self, post) # команды бота
    
    def updateSettings(self):
        with open(self.fileSettings, 'w') as file:
            file.write(json.dumps(self.settings))

MyDiscussionsBot()
