import re
import json

from typing import Optional
from datetime import datetime

from general import discbot, discmess

FILE_WARNS = 'configs/warns.json'

class WarnsHandler:
    def __init__(self, bot: discbot.DiscussionsBot):
        self.bot = bot

        self.commands_map = {
            'add': self._handle_add,
            '@': self._handle_add,
            'list': self._handle_list,
            'delete': self._handle_delete
        }
    
    def _handle_warn(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        if not ('sysop' in message['permission'] or 'threadmoderator' in message['permission']):
            return
        
        parts = message['full_command'].split(maxsplit=2)
        if len(parts) == 1:
            return # неверная команда
        
        subcommand = parts[1].lower()
        for command, handler in self.commands_map.items():
            if subcommand.startswith(command):
                return handler(message, data_reply)
    
    def _handle_add(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split('@', maxsplit=1)
        if len(parts) == 1:
            return # неверная команда
        
        username_with_reason = parts[1].strip()
        if username_with_reason == '':
            return # неверная команда
        
        parts = username_with_reason.split(':', maxsplit=1)
        username = parts[0].replace('_', ' ').strip()

        if len(parts) == 1:
            reason = 'без причины'
        else:
            reason = parts[1].strip()
        
        with open(FILE_WARNS, 'r') as file:
            data_warns = json.load(file)
        
        if not username in data_warns:
            if not self.bot.activity.get_user_id(username):
                return self._unknown_user(message, data_reply) # неизвестный участник
            
            data_warns[username] = []
        
        warn = {
            'moderator': message['user'],
            'reason': reason,
            'timestamp': message['timestamp'].strftime('%d.%m.%Y %H:%M:%S')
        }

        data_warns[username].append(warn)

        with open(FILE_WARNS, 'w') as file:
            json.dump(data_warns, file, indent=2)
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', предупреждение успешно добавлено ⚠️')
        reply.add_paragraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.add_text_to_last('warn delete @username: 1 2', strong=True).add_text_to_last(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.add_paragraph('📋 Текущий список предупреждений для участника ' + username + ':')
        # reply.addBulletList()

        # for warn in data_warns[username]:
        #     reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot.core.botname))
        return reply

    def _handle_list(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split('@', maxsplit=1)
        if len(parts) == 1:
            return # неверная команда
        
        username = parts[1].strip()
        if username == '':
            return # неверная команда
        
        with open(FILE_WARNS, 'r') as file:
            data_warns = json.load(file)
        
        if not username in data_warns:
            return self._unknown_user(message, data_reply) # неизвестный участник

        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', список активных предупреждений, выданных этому участнику ⚠️')
        # reply.addBulletList()

        # for warn in data_warns[username]:
        #     reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.add_paragraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.add_text_to_last('warn delete @username: 1 2', strong=True).add_text_to_last(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot.core.botname))
        return reply

    def _handle_delete(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split('@', maxsplit=1)
        if len(parts) == 1:
            return # неверная команда
        
        username_with_numbers = parts[1].strip()
        if username_with_numbers == '':
            return # неверная команда
        
        parts = username_with_numbers.split(':', maxsplit=1)
        username = parts[0].replace('_', ' ').strip()

        with open(FILE_WARNS, 'r') as file:
            data_warns = json.load(file)
        
        if not username in data_warns:
            return self._unknown_user(message, data_reply) # неизвестный участник
        
        if len(parts) == 1 or 'all' in parts[1]:
            data_warns[username] = []

        else:
            indexes_to_remove = [int(i) - 1 for i in re.findall(r'\d+', parts[1])]
            valid_indexes = [i for i in indexes_to_remove if 0 <= i < len(data_warns[username])]
            for i in sorted(valid_indexes, reverse=True):
                del data_warns[username][i]
        
        with open(FILE_WARNS, 'w') as file:
            json.dump(data_warns, file, indent=2)
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', предупреждение успешно добавлено ⚠️')
        reply.add_paragraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.add_text_to_last('warn delete @username: 1 2', strong=True).add_text_to_last(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.add_paragraph('📋 Текущий список предупреждений для участника ' + username + ':')
        # reply.addBulletList()

        # for warn in data_warns[username]:
        #     reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot.core.botname))
        return reply

    def _unknown_user(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', не удалось найти участника с таким именем ❗')
        reply.add_paragraph('Проверьте, что вы правильно указали имя — оно должно соответствовать имени пользователя на вики. Если имя состоит из нескольких слов, не забудьте про пробелы или символ @.')
        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot.core.botname))
        return reply
