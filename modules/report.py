import json

from typing import Optional

from general import discbot, discmess

FILE_SETTINGS = 'configs/settings.json'
FILE_REPORT = 'configs/report.json'

class Report:
    def __init__(self, bot: discbot.DiscussionsBot):
        self.bot = bot
    
    def handle(self, message: discmess.DiscussionsMessage, data_forbidden_words: list) -> None:
        content = message['jsonModel'].lower() # в комментариях к статьям почему-то нет rawContent
        if any(word in content for word in data_forbidden_words):
            self._create_report(message)
    
    def _create_report(self, message: discmess.DiscussionsMessage) -> None:
        match message['type']: # todo: см. moderation
            case 'FORUM':
                self.bot.moderation.report_post_discussion(message['post_id'])
            
            case 'WALL':
                self.bot.moderation.report_post_message_wall(message['post_id'])
            
            case 'ARTICLE_COMMENT':
                self.bot.moderation.report_post_article_comments(message['post_id'], self.bot.activity.get_page_title(message['forum_id']))

class ReportHandler:
    def __init__(self, bot: discbot.DiscussionsBot):
        self.bot = bot

        self.commands_map = {
            'on': self._handle_enable,
            'enable': self._handle_enable,
            'off': self._handle_disable,
            'disable': self._handle_disable
        }
    
    def _handle_report(self, message: discmess.DiscussionsMessage) -> Optional[discmess.DiscussionsMessage]:
        if not 'sysop' in message['permission']:
            return
        
        parts = message['full_command'].split(maxsplit=2)
        if len(parts) == 1:
            return # неверная команда
        
        with open('languages/{}/report.json'.format(self.bot.core.wikilang), 'r') as file:
            data_reply = json.load(file)
        
        subcommand = parts[1].lower()
        for command, handler in self.commands_map.items():
            if subcommand.startswith(command):
                return handler(message, data_reply)
    
    def _handle_enable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_SETTINGS, 'r') as file:
            data_report = json.load(file)
        
        with open(FILE_SETTINGS, 'w') as file:
            data_report['statusReport'] = True
            json.dump(data_report, file, indent=2)
        
        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['REPORT_ENABLE'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)

    def _handle_disable(self, message: discmess.DiscussionsMessage, data_reply: dict) -> discmess.DiscussionsMessage:
        with open(FILE_SETTINGS, 'r') as file:
            data_report = json.load(file)
        
        with open(FILE_SETTINGS, 'w') as file:
            data_report['statusReport'] = False
            json.dump(data_report, file, indent=2)
        
        replacements = {
            '$USERNOTIFICATION': {"mention_id": str(message['user_id']), "mention_text": message['user']},
            '$BOTOWNER': {"text": 'Зубенко Михаил Петрович', "link": '{}/Стена_обсуждения:Зубенко_Михаил_Петрович'.format(self.bot.core.wikilink)}
        }

        modified_template = discmess.DiscussionsMessage.replace_in_message_from_dict(data_reply['REPORT_DISABLE'], replacements)
        return discmess.DiscussionsMessage.from_dict(modified_template)
