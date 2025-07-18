import json

from typing import Optional
from datetime import datetime, timezone, timedelta

from general import discbot, discmess

FILE_SETTINGS = 'configs/settings.json'
FILE_AUTOGREETING = 'configs/autogreeting.json'

class Autogreeting:
    def __init__(self, bot: discbot.DiscussionsBot):
        self.bot = bot
    
    def handle(self, message: discmess.DiscussionsMessage, data_famous_users: list) -> list:
        if message['user_id'] in data_famous_users:
            return data_famous_users
        
        if message['type'] in ['EDIT', 'NEW', 'LOG', 'CATEGORIZE']: # todo: см. activity
            data_user_messages = self.bot.activity.get_user_contributions(user_id=message['user_id'], limit=1)
        else:
            data_user_messages = self.bot.activity.get_user_profile_activity(user_id=message['user_id'], limit=75)
        
        if (datetime.now(timezone.utc) - data_user_messages[0]['timestamp']) >= timedelta(hours=24):
            with open(FILE_AUTOGREETING, 'r') as file:
                data_autogreeting = json.load(file)
            self._create_autogreeting(message, data_autogreeting) # присылаем автоприветствие участнику

        data_famous_users.append(message['user_id']) # кэшируем его
        return data_famous_users
    
    def _create_autogreeting(self, message: discmess.DiscussionsMessage, data_autogreeting: dict) -> discmess.DiscussionsMessage:
        replacements = {
            '$USERNAME': {"text": message['user']},
            '$WIKINAME': {"text": self.bot.core.wikiname},
            '$PAGETITLE': {"text": message['thread'], "link": self.bot.activity.get_page_url(message)}
        }

        # заменяем переменные $USERNAME, $WIKI и $PAGETITLE в jsonModel и rawContent, сохраняя форматирование и добавляя ссылки
        modified_template = discmess.DiscussionsMessage.replace_in_message(data_autogreeting["rawContent"], data_autogreeting["jsonModel"], data_autogreeting["attachments"], replacements)
        create_autogreeting = discmess.DiscussionsMessage.from_dict(modified_template)
        self.bot.moderation.create_thread_message_wall(create_autogreeting, data_autogreeting['title'], user_id=message['user_id'])

class AutogreetingHandler:
    def __init__(self, bot: discbot.DiscussionsBot):
        self.bot = bot

        self.commands_map = {
            'on': self._handle_enable,
            'enable': self._handle_enable,
            'off': self._handle_disable,
            'disable': self._handle_disable,
            'test': self._handle_test,
            'title': self._handle_title,
            'content': self._handle_content,
            'message': self._handle_content
        }
    
    def _handle_greeting(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
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
            settings = json.load(file)
        
        with open(FILE_SETTINGS, 'w') as file:
            settings['statusAutogreeting'] = True
            json.dump(settings, file, indent=2)
        
        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['GREETING_ENABLE'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)

    def _handle_disable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_SETTINGS, 'r') as file:
            settings = json.load(file)
        
        with open(FILE_SETTINGS, 'w') as file:
            settings['statusAutogreeting'] = False
            json.dump(settings, file, indent=2)
        
        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$BOTOWNER': {"text": 'Зубенко Михаил Петрович', "link": '{}/Стена_обсуждения:Зубенко_Михаил_Петрович'.format(self.bot.core.wikilink)}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['GREETING_DISABLE'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)
    
    def _handle_test(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[None]:
        with open(FILE_SETTINGS, 'r') as file:
            settings = json.load(file)
            if not settings['statusAutogreeting']:
                return self._reply_disabled_module(message, data_reply) # автоприветствия выключены

        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.load(file)

        Autogreeting(self.bot)._create_autogreeting(message, data_autogreeting)

    def _handle_title(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split(':', maxsplit=1)
        if len(parts) == 1:
            return # неверная команда

        title = parts[1].strip()
        if title == '':
            return # неверная команда
        
        with open(FILE_SETTINGS, 'r') as file:
            settings = json.load(file)
            if not settings['statusAutogreeting']:
                return self._reply_disabled_module(message, data_reply) # автоприветствия выключены

        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.load(file)

        with open(FILE_AUTOGREETING, 'w') as file:
            data_autogreeting['title'] = title
            json.dump(data_autogreeting, file, indent=2)

        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$GREETINGTITLE': {"text": title}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['GREETING_TITLE'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)

    def _handle_content(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split(':', maxsplit=1)
        if len(parts) == 1:
            return # неверная команда

        model = json.loads(message['jsonModel'])
        content = model["content"][1:]
        if content == []:
            return # неверная команда
        
        with open(FILE_SETTINGS, 'r') as file:
            settings = json.load(file)
            if not settings['statusAutogreeting']:
                return self._reply_disabled_module(message, data_reply) # автоприветствия выключены
        
        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.load(file)
        
        raw_text = parts[1].strip()
        model["content"] = content
        message['attachments'].pop("polls", None)
        message['attachments'].pop("quizzes", None)
        
        with open(FILE_AUTOGREETING, 'w') as file:
            data_autogreeting["rawContent"] = raw_text
            data_autogreeting["jsonModel"] = model
            data_autogreeting["attachments"] = message['attachments']
            json.dump(data_autogreeting, file, indent=2)
        
        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['GREETING_CONTENT'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)
    
    def _reply_disabled_module(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        replacements = { # todo: добавить текст о связи с владельцем бота
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['GREETING_ERROR'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)
