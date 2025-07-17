import re

from . import disccore
from . import discmess

from typing import Optional
from datetime import datetime, timezone

class DiscussionsActivity:
    def __init__(self, bot: disccore.DiscussionsCore):
        self.bot = bot

    def get_wiki_activity(self, since: str, limit: int=100) -> list[dict]:
        edits = self.get_recent_changes(since, limit=limit)
        posts = self.get_social_activity(since, limit=limit)

        return sorted(edits + posts, key=lambda item: item['timestamp'])
    
    def get_recent_changes(self, since: str, limit: int=100) -> list[dict]:
        parameters = {
            'action': 'query',
            'list': 'recentchanges',
            'rcstart': since,
            'rcdir': 'newer', # список выводится от старых к новым правкам
            'rcexcludeuser': self.bot.botname, # игнорируем любые свои правки (от бота)
            'rcprop': 'user|userid|comment|timestamp|title|ids|size',
            'rcshow': '!anon|!bot', # игнорируем любые правки от анонимных участников и от других ботов
            'rclimit': str(limit),
            'format': 'json'
        }

        data = self.bot._get(self.bot._api_url, parameters)
        return self._parse_recent_changes(data['query']['recentchanges'])
    
    def get_social_activity(self, since: str, limit: str=100) -> list[dict]:
        parameters = {
            'controller': 'DiscussionPost',
            'method': 'getPosts',
            'limit': str(limit),
            'since': since[:-1] + '.000Z'
        }

        data = self.bot._get(self.bot._wikia_api_url, parameters)
        return self._parse_social_activity(data['_embedded']['doc:posts'])
    
    def get_user_contributions(self, username: Optional[str]=None, user_id: Optional[int]=None, limit: int=10) -> list[dict]:
        if not username and not user_id:
            raise ValueError("Need username, or user_id")
    
        parameters = {
            'action': 'query',
            'list': 'usercontribs',
            'uclimit': str(limit),
            'ucdir': 'newer', # список выводится от первой правки на вики
            'format': 'json'
        }

        if username:
            parameters['ucuser'] = username
        else:
            parameters['ucuserids'] = user_id
        
        data = self.bot._get(self.bot._api_url, parameters)
        return self._parse_recent_changes(data['query']['usercontribs'])
    
    def get_user_profile_activity(self, username: Optional[str]=None, user_id: Optional[int]=None, limit: int=10) -> list[dict]:
        if not username and not user_id:
            raise ValueError("Need username, or user_id")

        parameters = {
            'controller': 'DiscussionContribution',
            'method': 'getPosts',
            'userId': str(user_id) if user_id is not None else self.get_user_id(username),
            'limit': str(limit)
        }

        data = self.bot._get(self.bot._wikia_api_url, parameters)
        return self._parse_social_activity(data['_embedded']['doc:posts'])
    
    def _parse_recent_changes(self, content: list[dict]) -> list[dict]:
        ''' преобразует свежие правки или вклад участника к единому формату для DiscussionsBot '''
        posts = []

        for item in content: # todo: я думаю, что эти данные не нужны вовсе
            post_type = (
                item.get('type', '').upper()
                if 'type' in item
                else 'EDIT' # сделано для совместимости с вкладом участника - там отсутствует этот ключ
            )

            post = {
                'type': post_type, # тип правки: EDIT, NEW, LOG или CATEGORIZE
                'thread': item['title'], # название страницы
                'thread_id': item['pageid'], # ID страницы
                'post_id': item['revid'], # ID правки
                'user': item['user'], # имя участника
                'user_id': item['userid'], # ID участника
                'timestamp': datetime.strptime(item['timestamp'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc), # время в datetime
                'forum': None, # все страницы имеют None (даже в комментариях)
                'forum_id': item['ns'], # пространство имен
                'position': item['revid'], # ID правки
                'content': item['comment'], # комментарий к правке

                'ping_bot': False, # пинга бота априори нет
                'full_command': '',
                'permission': ''
            }

            posts.append(post)
        
        return posts
    
    def _parse_social_activity(self, content: list[dict]) -> list[dict]:
        ''' преобразует социальную активность или активность участника к единому формату для DiscussionsBot '''
        posts = []

        for item in content:
            # пропускаем сообщения анонимных участников и самого бота
            if item['createdBy']['id'] == '0' or item['createdBy']['id'] == str(self.bot.bot_id):
                continue
            
            post = {
                'type': item['_embedded']['thread'][0]['containerType'], # тип сообщения: FORUM, WALL или ARTICLE_COMMENT
                'thread': item['_embedded']['thread'][0]['title'], # название темы
                'thread_id': int(item['threadId']), # ID темы
                'post_id': int(item['id']), # ID сообщения
                'user': item['createdBy']['name'], # имя участника
                'user_id': int(item['createdBy']['id']), # ID участника
                'timestamp': datetime.fromtimestamp(item['creationDate']['epochSecond'], tz=timezone.utc), # время в datetime
                'forum': item['forumName'], # название форума (в случае страницы None)
                'forum_id': int(item['forumId']), # ID форума
                'position': item['position'], # позиция в теме
                'content': item['rawContent'], # содержание сообщения

                'ping_bot': False, # см. ниже
                'full_command': '',
                'permission': item['createdBy']['badgePermission'],

                'jsonModel': item['jsonModel'],
                'attachments': item['_embedded']['attachments'][0]
            }

            # проверка на пинг бота
            normalized = re.sub(r'\s+', ' ', post['content'].strip())
            if normalized.lower().startswith('@bot '):
                post['ping_bot'] = True
                post['full_command'] = normalized.split(maxsplit=1)[1]
            
            posts.append(post)
        
        # список выводится от старых к новым сообщениям и комментариям
        return list(reversed(posts))
    
    def get_user_id(self, username: str) -> int:
        ''' возвращает ID участника по его имени, если существует
            если пользователь не найден или аноним - возвращает 0 '''

        parameters = {
            'action': 'query',
            'list': 'users',
            'ususers': username,
            'format': 'json'
        }

        data = self.bot._get(self.bot._api_url, params=parameters)
        return data['query']['users'][0].get('userid', 0)

    def get_page_url(self, message: discmess.DiscussionsMessage) -> str:
        ''' формирует ссылку на страницу/сообщение в зависимости от его типа '''

        match message['type']:
            case 'EDIT' | 'NEW' | 'LOG' | 'CATEGORIZE':
                return '{}/wiki/{}'.format(self.bot.wikilink, message['thread'].replace(' ', '_'))
            
            case 'FORUM':
                url = '{}/f/p/{}'.format(self.bot.wikilink, message['thread_id'])
                return url if message['position'] == 1 else '{}/r/{}'.format(url, message['post_id'])
            
            case 'WALL':
                # в начале forum находится имя владельца, а потом всегда идет стандартная фраза Message Wall (13 символов)
                url = '{}/wiki/Message_Wall:{}?threadId={}'.format(self.bot.wikilink, message['forum'][:-13].replace(' ', '_'), message['thread_id'])
                return url if message['position'] == 1 else '{}#{}'.format(url, message['post_id'])
            
            case 'ARTICLE_COMMENT':
                url = '{}/wiki/{}?commentId={}'.format(self.bot.wikilink, self.get_page_title(message['forumd_id']), message['thread_id'])
                return url if message['position'] == 1 else '{}&replyId={}'.format(url, message['post_id'])
        
    def get_page_title(self, forum_id: int) -> str:
        parameters = {
            'controller': 'ArticleComments',
            'method': 'getArticleTitle',
            'stablePageId': str(forum_id),
            'format': 'json'
        }

        data = self.bot._get(self.bot._wikia_api_url, parameters)
        return data['title']
