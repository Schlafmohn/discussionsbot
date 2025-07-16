import re
import json

from general import discbot
from general import activity
from general import moderation
from general import discmess
from autogreeting import AutogreetingHandler

from datetime import datetime
from typing import Optional

class CommandHandler:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation

        self.commands_map = {
            'ping': self._handle_ping,
            'pong': self._handle_ping,
            'autogreeting': self._handle_autogreeting,
            'report on': self._handle_report_enable,
            'report enable': self._handle_report_enable,
            'report off': self._handle_report_disable,
            'report disable': self._handle_report_disable,
            'warn add': self._handle_warn_add,
            'warn list': self._handle_warn_list,
            'warn delete': self._handle_warn_delete,
            'random': self._handle_random
        }
    
    def handle(self, message: discmess.DiscussionsMessage) -> bool:
        if not message['ping_bot']:
            return False
        
        with open('languages/{}.json'.format(self.bot._wikilang), 'r') as file:
            data_reply = json.load(file)
        
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
                return self.moderation.create_reply_article_comment(reply, message['thread_id'], self.activity._get_page_title(message['forum_id']))
    
    def _handle_ping(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        reply = discmess.DiscussionsMessage()
        reply.addText(message['user'], strong=True).addText(', привет! Я, ').addText(self.bot._botname, strong=True)
        reply.addText(', – бот обсуждений, написанный абсолютно с нуля участником Зубенко Михаил Петрович. Если у тебя будут какие-то вопросы, лучше обращайся к нему. Держи даже ')
        reply.addText('ссылку', link='https://warriors-cats.fandom.com/ru/wiki/Стена_обсуждения:Зубенко_Михаил_Петрович')
        reply.addText('. Мне нет никакого смысла писать, я не обладаю даже встроенной функцией от Chat GPT 🏓')
        
        return reply
    
    def _handle_autogreeting(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        return self.autogreeting._handle_autogreeting(message, data_reply)

    def _handle_report_enable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        pass

    def _handle_report_disable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        pass

    def _handle_warn_add(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        pattern = r'warn add\s?@?(.+?)(?:\s?:\s?)(.+)'
        match = re.match(pattern, message['full_command'])

        if not match:
            return # неверная команда
        
        username = match.group(1).replace('_', ' ')
        reason = match.group(2)

        with open('../configs/warns.json', 'r') as file:
            data_warns = json.loads(file)
        
        if not username in data_warns:
            if not self.activity.get_user_id(username):
                return # неверная команда
            data_warns[username] = []
        
        warn = {
            'moderator': message['user'],
            'reason': reason,
            'timestamp': datetime.strptime(message['timestamp'], '%d.%m.%Y %H:%M:%S')
        }

        reply = discmess.DiscussionsMessage()
        reply.addText(message['user'], strong=True).addText(', предупреждение успешно добавлено ⚠️')
        reply.addParagraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.addText('warn delete @username: 1 2', strong=True).addText(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.addParagraph('📋 Текущий список предупреждений для участника ' + username + ':')
        reply.addBulletList()

        for warn in data_warns[username]:
            reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
    
    def _handle_warn_list(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        pattern = r'warn list\s?@?(.+)'
        match = re.match(pattern, message['full_command'])

        if not match:
            return # неверная команда
        
        username = match.group(1).replace('_', ' ')

        with open('../configs/warns.json', 'r') as file:
            data_warns = json.loads(file)
        
        if not username in data_warns:
            return # неверная команда
        
        reply = discmess.DiscussionsMessage()
        reply.addText(message['user'], strong=True).addText(', список активных предупреждений, выданных этому участнику ⚠️')
        reply.addBulletList()

        for warn in data_warns[username]:
            reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.addParagraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.addText('warn delete @username: 1 2', strong=True).addText(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
    
    def _handle_warn_delete(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        pattern = r'warn delete\s?@?(.+?)(?:\s?:\s?)(.+)'
        match = re.match(pattern, message['full_command'])

        if not match:
            return # неверная команда
        
        username = match.group(1).replace('_', ' ')
        list_to_remove = match.group(2)

        with open('../configs/warns.json', 'r') as file:
            data_warns = json.loads(file)
        
        if not username in data_warns:
            return # неверная команда
        
        if 'all' in list_to_remove:
            data_warns[username] = []
        else:
            indexes_to_remove = [int(i) - 1 for i in re.findall(r'\d+', list_to_remove)]
            valid_indexes = [i for i in indexes_to_remove if 0 <= i < len(data_warns)]

            for i in sorted(valid_indexes, reverse=True):
                del data_warns[i]
        
        reply = discmess.DiscussionsMessage()
        reply.addText(message['user'], strong=True).addText(', предупреждение успешно добавлено ⚠️')
        reply.addParagraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.addText('warn delete @username: 1 2', strong=True).addText(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.addParagraph('📋 Текущий список предупреждений для участника ' + username + ':')
        reply.addBulletList()

        for warn in data_warns[username]:
            reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
    
    def _handle_random(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        pass
