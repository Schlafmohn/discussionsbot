import re
import json

from general import discbot
from general import activity
from general import moderation
from general import message

from datetime import datetime
from typing import Optional

class Commands:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation

        self.commands_map = {
            'ping': self._handle_ping,
            'pong': self._handle_ping,
            'autogreeting on': self._handle_autogreeting_enable,
            'autogreeting enable': self._handle_autogreeting_enable,
            'autogreeting off': self._handle_autogreeting_disable,
            'autogreeting disable': self._handle_autogreeting_disable,
            'autogreeting title': self._handle_autogreeting_title,
            'autogreeting message': self._handle_autogreeting_message,
            'report on': self._handle_report_enable,
            'report enable': self._handle_report_enable,
            'report off': self._handle_report_disable,
            'report disable': self._handle_report_disable,
            'warn add': self._handle_warn_add,
            'warn list': self._handle_warn_list,
            'warn delete': self._handle_warn_delete,
            'random': self._handle_random
        }
    
    def handle(self, message: message.DiscussionsMessage) -> bool:
        if not message['ping_bot']:
            return False
        
        with open('languages/{}.json'.format(self.bot._wikilang), 'r') as file:
            data_reply = json.load(file.read())
        
        reply = message.DiscussionsMessage()
        lower_command = message['full_command'].lower()

        for command, handler in self.commands_map.item():
            if lower_command.startswith(command):
                reply = handler(message, data_reply)
                break
        
        if not reply:
            return False
        
        match message['type']:
            case 'FORUM':
                self.moderation.create_reply_discussion(reply, message['thread_id'])
            
            case 'WALL':
                self.moderation.create_reply_message_wall(reply, message['thread_id'], user_id=message['user_id'])
            
            case 'ARTICLE_COMMENT':
                self.moderation.create_reply_article_comment(reply, message['thread_id'], self.activity._get_page_title(message['forum_id']))

        return True
    
    def _handle_ping(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        reply = message.DiscussionsMessage()
        reply.addText(message['user'], strong=True).addText(', привет! Я, ').addText(self.bot._botname, strong=True)
        reply.addText(', – бот обсуждений, написанный абсолютно с нуля участником Зубенко Михаил Петрович. Если у тебя будут какие-то вопросы, лучше обращайся к нему. Держи даже ')
        reply.addText('ссылку', link='https://warriors-cats.fandom.com/ru/wiki/Стена_обсуждения:Зубенко_Михаил_Петрович')
        reply.addText('. Мне нет никакого смысла писать, я не обладаю даже встроенной функцией от Chat GPT 🏓')
        
        return reply
    
    def _handle_autogreeting_enable(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        pass

    def _handle_autogreeting_disable(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        pass

    def _handle_autogreeting_title(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        pass

    def _handle_autogreeting_message(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        pass

    def _handle_report_enable(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        pass

    def _handle_report_disable(self, message: message.DiscussionsMessage, data_reply: dict) -> message.DiscussionsMessage:
        pass

    def _handle_warn_add(self, message: message.DiscussionsMessage, data_reply: dict) -> Optional[message.DiscussionsMessage]:
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

        reply = message.DiscussionsMessage()
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
    
    def _handle_warn_list(self, message: message.DiscussionsMessage, data_reply: dict) -> Optional[message.DiscussionsMessage]:
        pattern = r'warn list\s?@?(.+)'
        match = re.match(pattern, message['full_command'])

        if not match:
            return # неверная команда
        
        username = match.group(1).replace('_', ' ')

        with open('../configs/warns.json', 'r') as file:
            data_warns = json.loads(file)
        
        if not username in data_warns:
            return # неверная команда
        
        reply = message.DiscussionsMessage()
        reply.addText(message['user'], strong=True).addText(', список активных предупреждений, выданных этому участнику ⚠️')
        reply.addBulletList()

        for warn in data_warns[username]:
            reply.addListItem(data_warns[username]['timestamp'] + ' от ' + data_warns[username]['moderator'] + '. Причина: ' + data_warns[username]['reason'])

        reply.addParagraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
        reply.addText('warn delete @username: 1 2', strong=True).addText(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

        reply.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
    
    def _handle_warn_delete(self, message: message.DiscussionsMessage, data_reply: dict) -> Optional[message.DiscussionsMessage]:
        pattern = r'warn add\s?@?(.+?)(?:\s?:\s?)(.+)'
        match = re.match(pattern, message['full_command'])

        if not match:
            return # неверная команда
        
        username = match.group(1).replace('_', ' ')
        list_to_remove = match.group(1)

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
        
        reply = message.DiscussionsMessage()
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


    

    
#     if 'update autopost' in post['content'].lower():
#         # обновление всего сообщения приветствия новых участников

#         with open('configs/autogreeting.json', 'r') as file:
#             dataAutogreeting = json.loads(file.read())

#         with open('configs/autogreeting.json', 'w') as file:
#             # нужно подправить `jsonModel`, потому что в нем первый `paragraph` относится к команде `update autopost`
#             jsonModel = json.loads(post['jsonModel'])
#             jsonModel['content'].pop(0)

#             dataAutogreeting['rawContent'] = post['content'].split('update autopost ')[1]
#             dataAutogreeting['jsonModel'] = jsonModel
#             dataAutogreeting['attachments'] = post['attachments']

#             print(dataAutogreeting, '\n\n\n', dataAutogreeting['jsonModel'])

#             file.write(json.dumps(dataAutogreeting))
        
#         replyPostCommand = discmess.DiscussionsMessage()
#         replyPostCommand.addText(dataReplyPost['UPDATE AUTOPOST'].replace('$USERNAME', post['user']))

#         self.myBot.createReplyMessageWall(
#             replyPostCommand,
#             threadID=post['threadID'],
#             userID=self.myBot.getBotUserID()
#         )

#         return


# def autogreetingEnable(self, post, replyPostCommand, dataReplyPost):
#     with open('configs/autogreeting.json', 'r') as file:
#         dataAutogreeting = json.loads(file.read())
        
#     with open('configs/autogreeting.json', 'w') as file:
#         dataAutogreeting['status'] = True
#         dataAutogreeting = json.loads(file.read())
    
#     replyPostCommand.addText(post['user'], strong=True).addText(', автоприветствия успешно включены ✅')
#     replyPostCommand.addParagraph('Теперь каждому новому участнику будут автоматически отправляться приветственное сообщение! Чтобы сделать его индивидуальнее, вы можете настроить:')
#     replyPostCommand.addBulletList('autogreeting title: [новый заголовок]', strong=True).addText(' — изменить заголовок')
#     replyPostCommand.addListItem('autogreeting message: [новое сообщение]', strong=True).addText(' — изменить текст приветствия')

#     replyPostCommand.addParagraph('📌 В тексте сообщения можно использовать следующие переменные:')
#     replyPostCommand.addBulletList('$USERNAME', strong=True).addText(' — имя нового участника')
#     replyPostCommand.addListItem('$WIKINAME', strong=True).addText(' — название вашей вики')
#     replyPostCommand.addListItem('$PAGENAME', strong=True).addText(' — название страницы или темы, где участник впервые проявил активность')

#     replyPostCommand.addParagraph('🔧 Текущие настройки автоприветствия:')
#     replyPostCommand.addParagraph('Заголовок:', strong=True).addText(dataAutogreeting['title'])
#     replyPostCommand.addParagraph('Сообщение:', strong=True).addText(dataAutogreeting['jsonModel'])

#     replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
#     replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))

# def autogreetingDisable(self, post, replyPostCommand, dataReplyPost):
#     with open('configs/autogreeting.json', 'r') as file:
#         dataAutogreeting = json.loads(file.read())
        
#     with open('configs/autogreeting.json', 'w') as file:
#         dataAutogreeting['status'] = False
#         dataAutogreeting = json.loads(file.read())
    
#     replyPostCommand.addText(post['user'], strong=True).addText(', автоприветствие новых участников выключено. Я больше не буду автоматически приветствовать пользователей при их первом действии. Если вы захотите снова включить эту функцию, используйте команду: ')
#     replyPostCommand.addText('autogreeting enable', strong=True).addText('.')

#     replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
#     replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))

# def autogreetingTitle(self, post, fullCommand, replyPostCommand, dataReplyPost):
#     newTitle = fullCommand[20:] # `autogreeting title: ` – 20 символов

#     with open('configs/autogreeting.json', 'r') as file:
#         dataAutogreeting = json.loads(file.read())
        
#     with open('configs/autogreeting.json', 'w') as file:
#         dataAutogreeting['title'] = newTitle
#         file.write(json.dumps(dataAutogreeting))
    
#     replyPostCommand.addText(post['user'], strong=True).addText(', заголовок автоприветствия успешно обновлен 🎉')
#     replyPostCommand.addParagraph('Чтобы изменить содержание самого автоматического сообщения новых участников, воспользуйтесь командой: ')
#     replyPostCommand.addText('autogreeting message: [новое сообщение]', strong=True).addText('.')

#     replyPostCommand.addParagraph('📌 В тексте приветствия вы можете использовать специальные переменные:')
#     replyPostCommand.addBulletList('$USERNAME', strong=True).addText(' — имя нового участника')
#     replyPostCommand.addListItem('$WIKINAME', strong=True).addText(' — название вашей вики')
#     replyPostCommand.addListItem('$PAGENAME', strong=True).addText(' — название страницы или темы, где участник впервые проявил активность')

#     replyPostCommand.addParagraph('🔧 Текущие настройки автоприветствия:')
#     replyPostCommand.addParagraph('Заголовок:', strong=True).addText(dataAutogreeting['title'])
#     replyPostCommand.addParagraph('Сообщение:', strong=True).addText(dataAutogreeting['jsonModel'])

#     replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
#     replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))



