import re
import json
import random

from general import discbot
from general import activity
from general import moderation
from general import discmess

from .warns import WarnsHandler
from .report import ReportHandler
from .autogreeting import AutogreetingHandler

from typing import Optional

class CommandHandler:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation

        self.commands_map = {
            'ping': self._handle_ping,
            'pong': self._handle_ping,
            'greeting': self._handle_greeting,
            'report': self._handle_report,
            'warn': self._handle_warn,
            'random': self._handle_random
        }
    
    def handle(self, message: discmess.DiscussionsMessage) -> bool:
        if not message['ping_bot']:
            return False
        
        with open('languages/{}.json'.format(self.bot._wikilang), 'r') as file:
            data_reply = json.loads(file.read())
        
        reply = discmess.DiscussionsMessage()
        lower_command = message['full_command'].lower()

        for command, handler in self.commands_map.items():
            if lower_command.startswith(command):
                reply = handler(message, data_reply)
                break
        
        if not reply:
            return False
        
        match message['type']: # todo !!!!!
            case 'FORUM':
                return self.moderation.create_reply_discussion(reply, message['thread_id'])
            
            case 'WALL':
                return self.moderation.create_reply_message_wall(reply, message['thread_id'], user_id=message['user_id'])
            
            case 'ARTICLE_COMMENT':
                return self.moderation.create_reply_article_comment(reply, message['thread_id'], self.activity.get_page_title(message['forum_id']))
    
    def _handle_ping(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', привет! Я, ').add_text_to_last(self.bot._botname, strong=True)
        reply.add_text_to_last(', – бот обсуждений, написанный абсолютно с нуля участником Зубенко Михаил Петрович. Если у тебя будут какие-то вопросы, лучше обращайся к нему. Держи даже ')
        reply.add_text_to_last('ссылку', link='https://warriors-cats.fandom.com/ru/wiki/Стена_обсуждения:Зубенко_Михаил_Петрович')
        reply.add_text_to_last('. Мне нет никакого смысла писать, я не обладаю даже встроенной функцией от Chat GPT 🏓')
        return reply
    
    def _handle_greeting(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        return AutogreetingHandler(self.bot, self.activity, self.moderation)._handle_greeting(message, data_reply)
    
    def _handle_report(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        return ReportHandler(self.bot, self.activity, self.moderation)._handle_report(message, data_reply)

    def _handle_warn(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        return WarnsHandler(self.bot, self.activity)._handle_warn(message, data_reply)
    
    def _handle_random(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
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
