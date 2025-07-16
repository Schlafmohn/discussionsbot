import re
import json

from general import discbot
from general import activity
from general import moderation
from general import discmess

from datetime import datetime, timezone, timedelta

FILE_AUTOGREETING = '../configs/autogreeting.json'

class Autogreeting:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation
    
    def handle(self, message: discmess.DiscussionsMessage, data_famous_users: list) -> list:
        if message['user_id'] in data_famous_users:
            return data_famous_users
        
        if message['type'] in ['EDIT', 'NEW', 'LOG', 'CATEGORIZE']:
            data_user_messages = self.activity.get_user_contributions(user_id=message['user_id'], limit=1)
        else:
            data_user_messages = self.activity.get_user_profile_activity(user_id=message['user_id'], limit=1)
        
        if (datetime.now(timezone.utc) - data_user_messages[0]['timestamp']) <= timedelta(hours=24):
            data_famous_users['famousUsers'].append(message['user_id']) # сохраняем его
            return data_famous_users
        
        with open(FILE_AUTOGREETING, 'r') as file:
            autogreeting = json.loads(file)
            autogreeting["jsonModel"] = json.loads(autogreeting["jsonModel"])
        
        replacements = {
            '$USERNAME': {"text": message['user']},
            '$WIKINAME': {"text": self.bot._wikiname},
            '$PAGETITLE': {"text": message['thread'], "link": self.activity.get_page_url(message)}
        }

        # заменяем переменные $USERNAME, $WIKI и $PAGETITLE в jsonModel и rawContent, сохраняя форматирование и добавляя ссылки
        autogreeting = self._process_autogreeting(autogreeting, replacements)

        create_autogreeting = discmess.DiscussionsMessage.from_existing(autogreeting["rawContent"], autogreeting["jsonModel"], autogreeting["attachments"])
        self.moderation.create_thread_message_wall(create_autogreeting, autogreeting["title"], user_id=message['user_id'])
        return data_famous_users

    def _process_autogreeting(self, autogreeting: dict, replacements: dict) -> dict:
        autogreeting["jsonModel"] = self._replace_in_node(autogreeting["jsonModel"], replacements)[0]

        for var, rep in replacements.items():
            autogreeting["rawContent"] = autogreeting["rawContent"].replace(var, rep["text"])
        return autogreeting
    
    @staticmethod
    def _replace_in_node(node: dict, replacements: dict) -> list:
        # сюда лучше не смотреть, это смерть мигом
        if node["type"] == "text":
            text = node["text"]

            for var, rep in replacements.items():
                if var in text:
                    before, _, after = text.partition(var)
                    nodes = []

                    if before:
                        nodes.append({"type": "text", "text": before, "marks": node.get("marks", [])})
                    new_node = {"type": "text", "text": rep["text"]}

                    if rep.get("link"):
                        new_node["marks"] = node.get("marks", []) + [{"type": "link", "attrs": {"href": rep["link"]}}]
                    else:
                        new_node["marks"] = node.get("marks", [])

                    nodes.append(new_node)
                    if after:
                        nodes += AutogreetingHandler.replace_in_node({"type": "text", "text": after, "marks": node.get("marks", [])}, replacements)

                    return nodes
            return [node]

        if "content" in node:
            node["content"] = [
                subnode
                for item in node["content"]
                for subnode in AutogreetingHandler.replace_in_node(item, replacements)
            ]

            return [node]
        return [node]

class AutogreetingHandler:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation

        self.commands_map = {
            'on': self._handle_autogreeting_enable,
            'enable': self._handle_autogreeting_enable,
            'off': self._handle_autogreeting_disable,
            'disable': self._handle_autogreeting_disable,
            'title': self._handle_autogreeting_title,
            'message': self._handle_autogreeting_message
        }
    
    def _handle_autogreeting(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        lower_command = message['full_command'].lower()
        for command, handler in self.commands_map.items():
            if command in lower_command:
                return handler(message, data_reply)
    
    def _handle_autogreeting_enable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_AUTOGREETING, 'r') as file:
            autogreeting = json.loads(file)
        
        with open(FILE_AUTOGREETING, 'w') as file:
            autogreeting['status'] = True
            file.write(json.dumps(autogreeting))
        
        reply = discmess.DiscussionsMessage()
    
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', автоприветствия успешно включены ✅')
        reply.add_paragraph('Теперь каждому новому участнику будут автоматически отправляться приветственное сообщение! Чтобы сделать его индивидуальнее, вы можете настроить:')
        # reply.addBulletList('autogreeting title: [новый заголовок]', strong=True).addText(' — изменить заголовок')
        # reply.addListItem('autogreeting message: [новое сообщение]', strong=True).addText(' — изменить текст приветствия')

        reply.add_paragraph('📌 В тексте сообщения можно использовать следующие переменные:')
        # reply.addBulletList('$USERNAME', strong=True).addText(' — имя нового участника')
        # reply.addListItem('$WIKINAME', strong=True).addText(' — название вашей вики')
        # reply.addListItem('$PAGENAME', strong=True).addText(' — название страницы или темы, где участник впервые проявил активность')

        reply.add_paragraph('🔧 Текущие настройки автоприветствия:')
        reply.add_paragraph('Заголовок:', strong=True).add_text_to_last(autogreeting['title'])
        reply.add_paragraph('Сообщение:', strong=True).add_text_to_last(autogreeting['jsonModel'])

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply

    def _handle_autogreeting_disable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_AUTOGREETING, 'r') as file:
            autogreeting = json.loads()
        
        with open(FILE_AUTOGREETING, 'w') as file:
            autogreeting['status'] = False
            file.write(json.dumps(autogreeting))
        
        reply = discmess.DiscussionsMessage()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', автоприветствие новых участников выключено. Я больше не буду автоматически приветствовать пользователей при их первом действии. Если вы захотите снова включить эту функцию, используйте команду: ')
        reply.add_text_to_last('autogreeting enable', strong=True).add_text_to_last('.')

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply

    def _handle_autogreeting_title(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        pattern = r'autogreeting title\s?:?\s?(.+)'
        match = re.match(pattern, message['full_command'])

        if not match:
            return # неверная команда
        
        title = match.group(1)

        with open(FILE_AUTOGREETING, 'r') as file:
            autogreeting = json.loads(file.read())

        with open(FILE_AUTOGREETING, 'w') as file:
            autogreeting['title'] = newTitle
            file.write(json.dumps(autogreeting))

        reply = discmess.DiscussionsMessage()
        reply.add_text_to_last(post['user'], strong=True).add_text_to_last(', заголовок автоприветствия успешно обновлен 🎉')
        reply.add_paragraph('Чтобы изменить содержание самого автоматического сообщения новых участников, воспользуйтесь командой: ')
        reply.add_text_to_last('autogreeting message: [новое сообщение]', strong=True).add_text_to_last('.')

        reply.add_paragraph('📌 В тексте приветствия вы можете использовать специальные переменные:')
        # reply.addBulletList('$USERNAME', strong=True).add_text_to_last(' — имя нового участника')
        # reply.addListItem('$WIKINAME', strong=True).add_text_to_last(' — название вашей вики')
        # reply.addListItem('$PAGENAME', strong=True).add_text_to_last(' — название страницы или темы, где участник впервые проявил активность')

        reply.add_paragraph('🔧 Текущие настройки автоприветствия:')
        reply.add_paragraph('Заголовок:', strong=True).add_text_to_last(autogreeting['title'])
        reply.add_paragraph('Сообщение:', strong=True).add_text_to_last(autogreeting['jsonModel'])

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply

    def _handle_autogreeting_message(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        pass
