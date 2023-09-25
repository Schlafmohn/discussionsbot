import json
import time

from datetime import datetime
from datetime import timezone
from datetime import timedelta

import discbot
import commands

class MyBot(discbot.DiscussionsBot, commands.CommandsMyBot):
    def __init__(self):
        with open('config.json', 'r') as file:
            config = json.loads(file.read())

        super().__init__(config['username'], config['password'], config['wiki'])

        self.wikiSettings = self.getWikiSettings()
        self.automatic = True

        while self.automatic:
            self.checkWikiActivity()
            # self.updateWikiSettings()
            time.sleep(5 * 60) # релакс 5 минут

    def getWikiSettings(self):
        with open('settings.json', 'r') as file:
            settings = json.loads(file.read())

        return settings

    def updateWikiSettings(self):
        with open('settings.json', 'w') as file:
            file.write(json.dumps(self.wikiSettings))

    def checkWikiActivity(self):
        # так как API MediaWiki и API Discussions работают по UTC, то и бот тоже должен работать по UTC — это значительно упрощает многие временные вещи
        nowTime = datetime.now(timezone.utc) - timedelta(seconds=7) # не знаю зачем минус 7 секунд, ну пусть будет :)
        print('Проверка времени:', datetime.strftime(nowTime, '%Y-%m-%dT%H:%M:%S.000Z'))

        # феншуй: сначала проверяем старые правки/сообщения/комментарии, переходя к новым, а не наоборот
        edits = self.getWikiActivity(self.wikiSettings['lastEdit'], dir='newer')
        time.sleep(3)

        for i in edits:
            print(i)
            print('\n\n')
            # if not i['userID'] in self.wikiSettings['idUsers']:
            #     print('Проверяем участника:', i['userID'], i['username'], i['containerType'], i['title'])
            #
            #     self.wikiSettings['idUsers'].append(i['userID'])
            #     if self.isUserNewOnWikiAndDiscussions(i['userID'], nowTime):
            #         print('Новый участник! Отправка сообщения…')
            #         self.autogreeting(i)

            # по задумке, не все команды бота должны одинаково работать на всей платформе обсуждений
            # какие-то команды доступны только для стен обсуждений, а какие-то только для комментариев

            # пример команды: @Bottovodstvo autogreeting new
            # command = i['rawContent'].split(username)[1] # patterns = re.compile(r'\w+').findall(i['rawContent'])

            if i['rawContent'][:len(self.username) + 1] == '@{}'.format(self.username):
                command = i['rawContent'].split(self.username + ' ')[1]
                subCommands = command.split(' ')
                print(subCommands)

                if i['containerType'] == 'FORUM':
                    self.forumCommands(subCommands, i)
                elif i['containerType'] == 'WALL':
                    self.wallCommands(subCommands, i)
                elif i['containerType'] == 'ARTICLE_COMMENT':
                    self.articleCommentCommands(subCommands, i)

            elif i['forumName'] == '{} Message Wall'.format(self.username):
                # на стенах обсуждениях участники не могут пинговать, поэтому проверяем: принадлежит ли эта стена боту?
                # если стена не бота, то проверяем следующее сообщение на присутствие команды
                subCommands = i['rawContent'].split(' ')
                self.wallCommands(subCommands, i)

        # миллисекунды добавляются в угоду прихоти API Discussions, без них параметр since будет некорректно работать
        # для API MediaWiki они необязательны, но и не мешают корректному отображению правок
        self.wikiSettings['lastEdit'] = datetime.strftime(nowTime, '%Y-%m-%dT%H:%M:%S.000Z')

    def forumCommands(self, subCommands, someEdit):
        if subCommands[0] == 'help':
            self.help(someEdit)

    def wallCommands(self, subCommands, someEdit):
        if subCommands[0] == 'help':
            self.help(someEdit)

        elif subCommands[0] == 'autogreeting':
            self.autogreetingSettings(subCommands[1], someEdit)

    def articleCommentCommands(self, subCommands, someEdit):
        if subCommands[0] == 'help':
            self.help(someEdit)

myBot = MyBot()
