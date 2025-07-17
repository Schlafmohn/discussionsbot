import json

from general import discbot
from general import activity
from general import moderation
from general import discmess

from typing import Optional

FILE_SETTINGS = 'configs/settings.json'
FILE_REPORT = 'configs/report.json'

class Report:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation
    
    def handle(self, message: discmess.DiscussionsMessage, data_forbidden_words: list) -> None:
        content = message['jsonModel'].lower() # в комментариях к статьям почему-то нет rawContent
        if any(word in content for word in data_forbidden_words):
            self._create_report(message)
    
    def _create_report(self, message: discmess.DiscussionsMessage) -> bool:
        match message['type']: # todo !!!!! кстати, нужно еще логику в activity пофиксить (c recent changes) 
            case 'FORUM':
                self.moderation.report_post_discussion(message['post_id'])
            
            case 'WALL':
                self.moderation.report_post_message_wall(message['post_id'])
            
            case 'ARTICLE_COMMENT':
                self.moderation.report_post_article_comments(message['post_id'], self.activity.get_page_title(message['forum_id']))

class ReportHandler:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation

        self.commands_map = {
            'on': self._handle_enable,
            'enable': self._handle_enable,
            'off': self._handle_disable,
            'disable': self._handle_disable
        }
    
    def _handle_report(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        if not 'sysop' in message['permission']:
            return
        
        parts = message['full_command'].split(maxsplit=2)
        if len(parts) == 1:
            return # неверная команда
        
        subcommand = parts[1].lower()
        for command, handler in self.commands_map.items():
            if subcommand.startswith(command):
                return handler(message, data_reply)
    
    def _handle_enable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_SETTINGS, 'r') as file:
            data_report = json.loads(file.read())
        
        with open(FILE_SETTINGS, 'w') as file:
            data_report['status'] = True
            file.write(json.dumps(data_report))
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', отчеты о нежелательных сообщениях включены 👁️‍🗨️')
        reply.add_paragraph('Теперь бот будет автоматически отправлять уведомления, если в сообщениях участников будут обнаружены подозрительные или запрещенные слова')
        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply

    def _handle_disable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_SETTINGS, 'r') as file:
            data_report = json.loads(file.read())
        
        with open(FILE_SETTINGS, 'w') as file:
            data_report['status'] = False
            file.write(json.dumps(data_report))
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', уведомления о сообщениях с нежелательными словами отключены. Я больше не буду отправлять отчеты о потенциально нарушающих сообщениях. Вы можете снова включить их в любое время командой ')
        reply.add_text_to_last('report enable', strong=True).add_text_to_last('.')
        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
