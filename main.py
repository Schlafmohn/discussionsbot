import json
import time

from general import discbot
from general import activity
from general import moderation

from modules import commands
from modules import autogreeting

from datetime import datetime

class MyDiscussionsBot:
    def __init__(self):
        with open('configs/config.json', 'r') as file:
            config = json.loads(file.read())
        
        self.bot = discbot.DiscussionsBot(config['username'], config['password'], config['wikilink'])

        self.activity = activity.DiscussionsActivity(self.bot)
        self.moderation = moderation.DiscussionsModeration(self.bot, self.activity)

        # проверяем autogreeting enable
        listNewMessages = self.activity.get_wiki_activity('2025-07-17T00:00:00Z')
        listNewMessages.reverse()
        for message in listNewMessages[:1]:
            commands.CommandHandler(self.bot, self.activity, self.moderation).handle(message)
            

        # self.autogreeting = Autogreeting
        # self.commands = Commands

        # self.fileSettings = 'configs/settings.json'
        # with open(self.fileSettings, 'r') as file:
        #     self.settings = json.loads(file.read())
        
        # listNewMessages = self.activity.get_wiki_activity(self.settings['lastCheck'])
        
        # while True:
        #     # для успешной работы бота, сначала соберем все свежие правки и социальную активность на вики
        #     listNewMessages = self.myBot.activity.get_wiki_activity(self.settings['lastCheck'])

        #     self.workMyBot(listNewMessages)
        #     self.updateSettings()
            
        #     time.sleep(60 * 5) # каждые 5 минут бот будет подхватывать новые данные с вики
    
    def workMyBot(self, listNewMessages):
        for post in listNewMessages:
            autogreeting.autogreeting(self, post) # автоприветствие новых участников
            commands.commands(self, post) # команды бота
            time.sleep(15)
    
    def updateSettings(self):
        with open(self.fileSettings, 'w') as file:
            file.write(json.dumps(self.settings))

if __name__ == '__main__':
    MyDiscussionsBot()
