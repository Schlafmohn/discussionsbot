import json
import time
import random
import signal

from datetime import datetime, timedelta

from general import discbot
from modules import commands, report, autogreeting

FILE_SETTINGS = 'configs/settings.json'

class MyDiscussionsBot:
    def __init__(self):
        with open('configs/config.json', 'r') as file:
            config = json.load(file)
        
        self.bot = discbot.DiscussionsBot(config['username'], config['password'], config['wikilink'])

        with open(FILE_SETTINGS, 'r') as file:
            self.settings = json.load(file)
        
        self.autogreeting = autogreeting.Autogreeting(self.bot)
        self.report = report.Report(self.bot)
        self.commands = commands.CommandHandler(self.bot)

        self.running = True
    
    def run(self):
        while self.running:
            list_messages = self.bot.activity.get_wiki_activity(self.settings['lastCheck'])

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
        
        self.update_settings()
    
    def update_settings(self):
        with open(FILE_SETTINGS, 'w') as file:
            json.dump(self.settings, file, indent=2)

def handle_exit(signum, frame):
    bot.running = False

if __name__ == '__main__':
    bot = MyDiscussionsBot()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    bot.run()
