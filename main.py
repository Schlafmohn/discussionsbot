import json
import time
import random

from general import discbot
from general import activity
from general import moderation

from modules import commands
from modules import report
from modules import autogreeting

from datetime import datetime, timedelta

FILE_SETTINGS = 'configs/settings.json'

class MyDiscussionsBot:
    def __init__(self):
        with open('configs/config.json', 'r') as file:
            config = json.loads(file.read())
        
        self.bot = discbot.DiscussionsBot(config['username'], config['password'], config['wikilink'])
        self.activity = activity.DiscussionsActivity(self.bot)
        self.moderation = moderation.DiscussionsModeration(self.bot, self.activity)

        with open(FILE_SETTINGS, 'r') as file:
            self.settings = json.loads(file.read())
        
        self.autogreeting = autogreeting.Autogreeting(self.bot, self.activity, self.moderation)
        self.report = report.Report(self.bot, self.activity, self.moderation)
        self.commands = commands.CommandHandler(self.bot, self.activity, self.moderation)
    
    def run(self):
        while True:
            list_messages = self.activity.get_wiki_activity(self.settings['lastCheck'])

            for message in list_messages:
                if self.settings['statusAutogreeting']:
                    self.settings['famousUsers'] = self.autogreeting.handle(message, self.settings['famousUsers'])
            
                if self.settings['statusReport']:
                    self.report.handle(message, self.settings['forbiddenWords'])
            
                self.commands.handle(message)
        
            if list_messages:
                self.settings['lastCheck'] = (list_messages[-1]['timestamp'] + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
            self.update_settings()
            time.sleep(random.uniform(5 * 60, 15 * 60))
    
    def update_settings(self):
        with open(FILE_SETTINGS, 'w') as file:
            file.write(json.dumps(self.settings))

if __name__ == '__main__':
    bot = MyDiscussionsBot()
    bot.run()
