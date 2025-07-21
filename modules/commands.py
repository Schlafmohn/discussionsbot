import json
import random

from typing import Optional

from .warns import WarnsHandler
from .report import ReportHandler
from .autogreeting import AutogreetingHandler

from general import discbot, discmess

class CommandHandler:
    def __init__(self, bot: discbot.DiscussionsBot):
        self.bot = bot

        self.commands_map = {
            'ping': self._handle_ping,
            'pong': self._handle_ping,
            'greeting': self._handle_greeting,
            'report': self._handle_report,
            'warn': self._handle_warn,
            'random': self._handle_random
        }
    
    def handle(self, message: discmess.DiscussionsMessage) -> None:
        if not message['ping_bot']:
            return
        
        reply = None
        lower_command = message['full_command'].lower()

        for command, handler in self.commands_map.items():
            if lower_command.startswith(command):
                reply = handler(message)
                break
        
        if not reply:
            return
        
        match message['type']: # todo: см. moderation
            case 'FORUM':
                self.bot.moderation.create_reply_discussion(reply, message['thread_id'])
            
            case 'WALL':
                self.bot.moderation.create_reply_message_wall(reply, message['thread_id'], user_id=message['user_id'])
            
            case 'ARTICLE_COMMENT':
                self.bot.moderation.create_reply_article_comment(reply, message['thread_id'], self.bot.activity.get_page_title(message['forum_id']))
    
    def _handle_ping(self, message: discmess.DiscussionsMessage) -> discmess.DiscussionsMessage:
        with open('languages/{}/commands.json'.format(self.bot.core.wikilang), 'r') as file:
            data_reply = json.load(file)['PING']

        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$BOTOWNER': {"text": 'Зубенко Михаил Петрович', "link": '{}/Стена_обсуждения:Зубенко_Михаил_Петрович'.format(self.bot.core.wikilink)}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply, replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)
    
    def _handle_greeting(self, message: discmess.DiscussionsMessage) -> Optional[discmess.DiscussionsMessage]:
        return AutogreetingHandler(self.bot)._handle_greeting(message)
    
    def _handle_report(self, message: discmess.DiscussionsMessage) -> discmess.DiscussionsMessage:
        return ReportHandler(self.bot)._handle_report(message)

    def _handle_warn(self, message: discmess.DiscussionsMessage) -> Optional[discmess.DiscussionsMessage]:
        return WarnsHandler(self.bot)._handle_warn(message)
    
    def _handle_random(self, message: discmess.DiscussionsMessage) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split(':', maxsplit=1)
        if len(parts) == 1:
            return # неверная команда
        
        elements = parts[1].strip()
        if elements == '':
            return # неверная команда
        
        values = [x.strip() for x in elements.split(',')]
        random_item = random.choice(values)
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', ').add_text_to_last('мудрый бот поглядел в хрустальный шар и выбрал:', italic=True)
        reply.add_paragraph(random_item, strong=True).add_text_to_last(' — да пребудет с тобой удача! ✨')
        return reply
