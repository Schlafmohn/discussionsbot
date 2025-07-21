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
    
    def _handle_warn(self, message: discmess.DiscussionsMessage) -> Optional[discmess.DiscussionsMessage]:
        if not ('sysop' in message['permission'] or 'threadmoderator' in message['permission']):
            return
        
        parts = message['full_command'].split(maxsplit=2)
        if len(parts) == 1:
            return # неверная команда
        
        with open('languages/{}/warns.json'.format(self.bot.core.wikilang), 'r') as file:
            data_reply = json.load(file)
        
        subcommand = parts[1].lower()
        for command, handler in self.commands_map.items():
            if subcommand.startswith(command):
                return handler(message, data_reply)
    
    @staticmethod # todo: построить внутренний «рендерер» для таких шаблонов — вроде как мини-библиотеку и переместить это куда-нибудь
    def build_warn_paragraph(index: int, moderator: str, reason: str, timestamp: str):
        # todo: добавить, что нарушений нет
        return {"type": "paragraph", "content": [{"type": "text", "text": f"{index}. [{timestamp}, {moderator}] — {reason}"}]}
    
    @staticmethod
    def inject_paragraphs(template: dict, marker_text: str, new_paragraphs: list) -> dict:
        """
        заменяет параграф с текстом-маркером в jsonModel и rawContent на список новых параграфов
        """

        # копируем список параграфов, чтобы избежать нежелательных мутаций
        content = template["jsonModel"]["content"].copy()

        # ищем индекс абзаца, содержащего текстовый узел с маркером
        marker_index = next((
            i for i, block in enumerate(content)
            if block.get("type") == "paragraph" and any(item.get("type") == "text" and item.get("text", "").strip() == marker_text
                for item in block.get("content", []))
            ),
            None
        )

        # если нашли нужный абзац — заменим его на новые
        if marker_index is not None:
            content = content[:marker_index] + new_paragraphs + content[marker_index + 1:]
            template["jsonModel"]["content"] = content

        # сгенерируем замену в rawContent на основе текстов из новых параграфов
        lines = []
        for para in new_paragraphs:
            if para.get("type") != "paragraph":
                continue

            texts = [
                node.get("text", "")
                for node in para.get("content", [])
                if node.get("type") == "text"
            ]

            line = "".join(texts).strip()

            if line:
                lines.append(line)

        raw_replacement = " ".join(lines)

        # заменим в rawContent
        if "rawContent" in template and isinstance(template["rawContent"], str):
            template["rawContent"] = template["rawContent"].replace(marker_text, raw_replacement)

        return template
    
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

        user_id = self.bot.activity.get_user_id(username)
        if not user_id:
            return self._unknown_user(message, data_reply) # неизвестный участник
        
        if not username in data_warns:
            data_warns[username] = []
        
        warn = {
            'moderator': message['user'],
            'reason': reason,
            'timestamp': message['timestamp'].strftime('%d.%m.%Y %H:%M:%S')
        }

        data_warns[username].append(warn)

        with open(FILE_WARNS, 'w') as file:
            json.dump(data_warns, file, indent=2)
        
        replacements = {
            '$MODERATORNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$USERNOTIFICATION': {"mention_id": user_id, "mention_text": username},
            '$USERNAME': {"text": username}
        }

        # заменяем переменную $LISTWARNS на список предупреждений новых параграфов
        warn_paragraphs = [WarnsHandler.build_warn_paragraph(i + 1, w['timestamp'], w['moderator'], w['reason']) for i, w in enumerate(data_warns[username])]
        updated_template = WarnsHandler.inject_paragraphs(data_reply['WARN_ADD'], '$LISTWARNS', warn_paragraphs)

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(updated_template, replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)

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
        
        replacements = {
            '$MODERATORNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$USERNAME': {"text": username}
        }

        # заменяем переменную $LISTWARNS на список предупреждений новых параграфов
        warn_paragraphs = [WarnsHandler.build_warn_paragraph(i + 1, w['timestamp'], w['moderator'], w['reason']) for i, w in enumerate(data_warns[username])]
        updated_template = WarnsHandler.inject_paragraphs(data_reply['WARN_LIST'], '$LISTWARNS', warn_paragraphs)

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(updated_template, replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)

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

            if not valid_indexes:
                return self._invalid_indexes(message, data_reply)
            
            for i in sorted(valid_indexes, reverse=True):
                del data_warns[username][i]
        
        with open(FILE_WARNS, 'w') as file:
            json.dump(data_warns, file, indent=2)
        
        replacements = {
            '$MODERATORNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$USERNAME': {"text": username}
        }

        # заменяем переменную $LISTWARNS на список предупреждений новых параграфов
        warn_paragraphs = [WarnsHandler.build_warn_paragraph(i + 1, w['timestamp'], w['moderator'], w['reason']) for i, w in enumerate(data_warns[username])]
        updated_template = WarnsHandler.inject_paragraphs(data_reply['WARN_DELETE'], '$LISTWARNS', warn_paragraphs)

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(updated_template, replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)

    def _unknown_user(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        replacements = {
            '$MODERATORNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$BOTOWNER': {"text": 'Зубенко Михаил Петрович', "link": '{}/Стена_обсуждения:Зубенко_Михаил_Петрович'.format(self.bot.core.wikilink)}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['WARN_ERROR'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)
    
    def _invalid_indexes(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        return
