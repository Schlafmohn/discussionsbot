import json

from general import discbot
from general import activity
from general import moderation
from general import discmess

from typing import Optional
from datetime import datetime, timezone, timedelta

FILE_AUTOGREETING = 'configs/autogreeting.json'

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
            data_user_messages = self.activity.get_user_profile_activity(user_id=message['user_id'], limit=75)
        
        if (datetime.now(timezone.utc) - data_user_messages[0]['timestamp']) >= timedelta(hours=24):
            with open(FILE_AUTOGREETING, 'r') as file:
                data_autogreeting = json.loads(file.read())

            create_autogreeting = self._create_autogreeting(message, data_autogreeting)
            self.moderation.create_thread_message_wall(create_autogreeting, data_autogreeting['title'], user_id=message['user_id'])

        data_famous_users['famousUsers'].append(message['user_id']) # сохраняем его
        return data_famous_users
    
    def _create_autogreeting(self, message: discmess.DiscussionsMessage, data_autogreeting: dict) -> bool:
        replacements = {
            '$USERNAME': {"text": message['user']},
            '$WIKINAME': {"text": self.bot._wikiname},
            '$PAGETITLE': {"text": message['thread'], "link": self.activity.get_page_url(message)}
        }

        # заменяем переменные $USERNAME, $WIKI и $PAGETITLE в jsonModel и rawContent, сохраняя форматирование и добавляя ссылки
        data_autogreeting = self._process_autogreeting(data_autogreeting, replacements)

        create_autogreeting = discmess.DiscussionsMessage.from_existing(data_autogreeting["rawContent"], data_autogreeting["jsonModel"], data_autogreeting["attachments"])
        return self.moderation.create_thread_message_wall(create_autogreeting, data_autogreeting['title'], user_id=message['user_id'])

    def _process_autogreeting(self, autogreeting: dict, replacements: dict) -> dict:
        autogreeting["jsonModel"] = Autogreeting._replace_in_node(autogreeting["jsonModel"], replacements)[0]

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
                        nodes += Autogreeting._replace_in_node({"type": "text", "text": after, "marks": node.get("marks", [])}, replacements)

                    return nodes
            return [node]

        if "content" in node:
            node["content"] = [
                subnode
                for item in node["content"]
                for subnode in Autogreeting._replace_in_node(item, replacements)
            ]

            return [node]
        return [node]

class AutogreetingHandler:
    def __init__(self, bot: discbot.DiscussionsBot, activity: activity.DiscussionsActivity, moderation: moderation.DiscussionsModeration):
        self.bot = bot
        self.activity = activity
        self.moderation = moderation

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
            print('A')
            return
        
        parts = message['full_command'].split(maxsplit=2)
        if len(parts) == 1:
            print('B')
            return # неверная команда
        
        subcommand = parts[1].lower()
        for command, handler in self.commands_map.items():
            if subcommand.startswith(command):
                return handler(message, data_reply)
        
        print('C')
    
    def _handle_enable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.loads(file.read())
        
        with open(FILE_AUTOGREETING, 'w') as file:
            data_autogreeting['status'] = True
            file.write(json.dumps(data_autogreeting))
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', автоприветствия успешно включены ✅')
        reply.add_paragraph('Теперь каждому новому участнику будут автоматически отправляться приветственное сообщение! Чтобы сделать его индивидуальнее, вы можете настроить:')
        # reply.addBulletList('autogreeting title: [новый заголовок]', strong=True).addText(' — изменить заголовок')
        # reply.addListItem('autogreeting message: [новое сообщение]', strong=True).addText(' — изменить текст приветствия')

        reply.add_paragraph('📌 В тексте сообщения можно использовать следующие переменные:')
        # reply.addBulletList('$USERNAME', strong=True).addText(' — имя нового участника')
        # reply.addListItem('$WIKINAME', strong=True).addText(' — название вашей вики')
        # reply.addListItem('$PAGENAME', strong=True).addText(' — название страницы или темы, где участник впервые проявил активность')

        reply.add_paragraph('🔧 Текущие настройки автоприветствия:')
        reply.add_paragraph('Заголовок:', strong=True).add_text_to_last(data_autogreeting['title'])
        # reply.add_paragraph('Сообщение:', strong=True).add_text_to_last(data_autogreeting['jsonModel'])

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply

    def _handle_disable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.loads(file.read())
        
        with open(FILE_AUTOGREETING, 'w') as file:
            data_autogreeting['status'] = False
            file.write(json.dumps(data_autogreeting))
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', автоприветствие новых участников выключено. Я больше не буду автоматически приветствовать пользователей при их первом действии. Если вы захотите снова включить эту функцию, используйте команду: ')
        reply.add_text_to_last('autogreeting enable', strong=True).add_text_to_last('.')

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
    
    def _handle_test(self, message: discmess.DiscussionsMessage, data_reply: dict) -> None:
        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.loads(file.read())
        
        if not data_autogreeting['status']:
            print('D')
            self._reply_disabled_module(message, data_reply)
            return self._reply_disabled_module(message, data_reply) # автоприветствия выключены

        Autogreeting(self.bot, self.activity, self.moderation)._create_autogreeting(message, data_autogreeting)

    def _handle_title(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split(':', maxsplit=1)
        if len(parts) == 1:
            print('E')
            return # неверная команда

        title = parts[1].strip()
        if title == '':
            print('F')
            return # неверная команда

        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.loads(file.read())
        
        if not data_autogreeting['status']:
            print('G') # дошел до сюдава, следующий — H
            return self._reply_disabled_module(message, data_reply) # автоприветствия выключены

        with open(FILE_AUTOGREETING, 'w') as file:
            data_autogreeting['title'] = title
            file.write(json.dumps(data_autogreeting))

        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', заголовок автоприветствия успешно обновлен 🎉')
        reply.add_paragraph('Чтобы изменить содержание самого автоматического сообщения новых участников, воспользуйтесь командой: ')
        reply.add_text_to_last('autogreeting message: [новое сообщение]', strong=True).add_text_to_last('.')

        reply.add_paragraph('📌 В тексте приветствия вы можете использовать специальные переменные:')
        # reply.addBulletList('$USERNAME', strong=True).add_text_to_last(' — имя нового участника')
        # reply.addListItem('$WIKINAME', strong=True).add_text_to_last(' — название вашей вики')
        # reply.addListItem('$PAGENAME', strong=True).add_text_to_last(' — название страницы или темы, где участник впервые проявил активность')

        reply.add_paragraph('🔧 Текущие настройки автоприветствия:')
        reply.add_paragraph('Заголовок:', strong=True).add_text_to_last(data_autogreeting['title'])
        # reply.add_paragraph('Сообщение:', strong=True).add_text_to_last(data_autogreeting['jsonModel'])

        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply

    def _handle_content(self, message: discmess.DiscussionsMessage, data_reply: dict) -> Optional[discmess.DiscussionsMessage]:
        parts = message['full_command'].split(':', maxsplit=1)
        if len(parts) == 1:
            print('H')
            return # неверная команда

        model = message['jsonModel']
        content = model["content"][1:]
        if content == []:
            print('I')
            return # неверная команда
        
        with open(FILE_AUTOGREETING, 'r') as file:
            data_autogreeting = json.loads(file.read())
        
        if not data_autogreeting['status']:
            print('J')
            return self._reply_disabled_module(message, data_reply) # автоприветствия выключены
        
        raw_text = parts[1].strip()
        model["content"] = content
        message['attachments'].pop("polls", None)
        message['attachments'].pop("quizzes", None)
        
        with open(FILE_AUTOGREETING, 'w') as file:
            data_autogreeting["rawContent"] = raw_text
            data_autogreeting["jsonModel"] = model
            data_autogreeting["attachments"] = message['attachments']
            file.write(json.dumps(data_autogreeting))
        
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', заголовок автоприветствия успешно обновлен 🎉')
        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
    
    def _reply_disabled_module(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        reply = discmess.DiscussionsMessage().add_paragraph()
        reply.add_text_to_last(message['user'], strong=True).add_text_to_last(', автоприветствия в данный момент отключены 🔕')
        reply.add_paragraph('Чтобы включить автоматические приветствия новых участников, используйте команду: ')
        reply.add_text_to_last('autogreeting enable', strong=True)
        reply.add_paragraph('📚 Полный список команд: ').add_text_to_last('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
        reply.add_text_to_last('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.bot._botname))
        return reply
