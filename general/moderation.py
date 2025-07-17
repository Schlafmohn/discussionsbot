from . import disccore
from . import activity
from . import discmess

from typing import Optional

class DiscussionsModeration:
    def __init__(self, bot: disccore.DiscussionsCore, activity: activity.DiscussionsActivity):
        self.bot = bot
        self.activity = activity # todo: есть идея объединить методы в один

    def create_thread_discussion(self, message: discmess.DiscussionsMessage, title: str, forum_id: int) -> None:
        parameters = {
            'controller': 'DiscussionThread',
            'method': 'create',
            'forumId': str(forum_id)
        }

        data = {
            'MIME Type': 'application/json',
            'Encoding': 'utf-8',
            'Request Data': {
                'body': message.build_raw_text(),
                'jsonModel': message.build_raw_model(),
                'attachments': message.build_raw_attachments(),
                'forumId': str(forum_id),
                'siteId': str(self.bot.wiki_id),
                'title': title,
                'source': 'DESKTOP_WEB_FEPO',
                'funnel': 'TEXT',
                'articleIds': []
            }
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)

    def create_reply_discussion(self, message: discmess.DiscussionsMessage, thread_id: int) -> None:
        parameters = {
            'controller': 'DiscussionPost',
            'method': 'create'
        }

        data = {
            'MIME Type': 'application/json',
            'Encoding': 'utf-8',
            'Request Data': {
                'body': message.build_raw_text(),
                'jsonModel': message.build_raw_model(),
                'attachments': message.build_raw_attachments(),
                'siteId': str(self.bot.wiki_id),
                'source': 'DESKTOP_WEB_FEPO',
                'threadId': str(thread_id)
            }
        }
        
        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def delete_post_discussion(self, thread_id: Optional[int]=None, post_id: Optional[int]=None) -> None:
        if not thread_id and not post_id:
            raise ValueError("Need thread_id, or post_id")

        parameters = {
            'controller': 'DiscussionThread',
            'method': 'delete'
        }

        if thread_id:
            parameters['threadId'] = str(thread_id)
        else:
            parameters['postId'] = str(post_id)
        
        data = {
            'MIME Type': 'multipart/form-data',
            'Boundary': '----WebKitFormBoundaryep0uj55I2xhFAxby',
            'Request Data': '------WebKitFormBoundaryep0uj55I2xhFAxby\nContent-Disposition: form-data; name="suppressContent"\n\nfalse\n------WebKitFormBoundaryep0uj55I2xhFAxby--'
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def report_post_discussion(self, post_id: int) -> None:
        parameters = {
            'controller': 'DiscussionModeration',
            'method': 'reportPost',
            'postId': str(post_id)
        }

        self.bot._post(self.bot._wikia_api_url, parameters)
    
    def lock_lost_discussion(self, thread_id: int) -> None:
        parameters = {
            'controller': 'DiscussionModeration',
            'method': 'lock',
            'threadId': str(thread_id)
        }

        self.bot._post(self.bot._wikia_api_url, parameters)
    
    def create_thread_message_wall(self, message: discmess.DiscussionsMessage, title: str, username: Optional[str]=None, user_id: Optional[int]=None) -> None:
        if not username and not user_id:
            raise ValueError("Need username, or user_id")

        parameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'createThread',
            'format': 'json'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self._get_token(),
            'wallOwnerId': str(user_id),
            'title': title,
            'rawContent': message.build_raw_text(),
            'jsonModel': message.build_raw_model(),
            'attachments': message.build_raw_attachments()
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def create_reply_message_wall(self, message: discmess.DiscussionsMessage, thread_id: int, username: Optional[str]=None, user_id: Optional[int]=None) -> None:
        if not username and not user_id:
            raise ValueError("Need username, or user_id")

        parameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'createReply',
            'format': 'json'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self._get_token(),
            'wallOwnerId': str(user_id) if user_id is not None else self.activity.get_user_id(username),
            'threadId': str(thread_id),
            'rawContent': message.build_raw_text(),
            'jsonModel': message.build_raw_model(),
            'attachments': message.build_raw_attachments()
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def delete_post_message_wall(self, thread_id: Optional[int]=None, post_id: Optional[int]=None, username: Optional[str]=None, user_id: Optional[str]=None) -> None:
        if not username and not user_id:
            raise ValueError("Need username, or user_id")
        
        if not thread_id and not post_id:
            raise ValueError("Need thread_id, or post_id")

        parameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'format': 'json'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self._get_token(),
            'wallOwnerId': str(user_id) if user_id is not None else self.activity.get_user_id(username),
            'suppressContent': 'false'
        }

        if thread_id:
            parameters['method'] = 'delete',
            data['postId'] = str(thread_id)
        else:
            parameters['method'] = 'deleteReply',
            data['postId'] = str(post_id)

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def report_post_message_wall(self, post_id: int) -> None:
        parameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'reportPost',
            'format': 'json'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self._get_token(),
            'postId': str(post_id)
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def lock_post_message_wall(self, thread_id: int, username: Optional[str]=None, user_id: Optional[int]=None) -> None:
        if not username and not user_id:
            raise ValueError("Need username, or user_id")

        parameters = {
            'controller': 'Fandom\\MessageWall\\MessageWall',
            'method': 'lockThread',
            'format': 'json'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'token': self._get_token(),
            'wallOwnerId': str(user_id) if user_id is not None else self.activity.get_user_id(username),
            'threadId': str(thread_id)
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def create_thread_article_comment(self, message: discmess.DiscussionsMessage, pagetitle: str) -> None:
        parameters = {
            'controller': 'ArticleCommentsController',
            'method': 'postNewCommentThread'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'title': pagetitle,
            'namespace': '0',
            'token': self._get_token(),
            'jsonModel': message.build_raw_model(),
            'attachments': message.build_attachments()
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def create_reply_article_comment(self, message: discmess.DiscussionsMessage, thread_id: int, pagetitle: str) -> None:
        parameters = {
            'controller': 'ArticleCommentsController',
            'method': 'postNewCommentReply'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'threadId': str(thread_id),
            'title': pagetitle,
            'namespace': '0',
            'token': self._get_token(),
            'jsonModel': message.build_raw_model(),
            'attachments': message.build_raw_attachments()
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def delete_post_article_comment(self, post_id: int, pagetitle: str) -> None:
        parameters = {
            'controller': 'ArticleCommentsController',
            'method': 'deletePost'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'postId': str(post_id),
            'token': self._get_token(),
            'suppressContent': 'false',
            'title': pagetitle,
            'namespace': '0'
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def report_post_article_comments(self, post_id: int, pagetitle: str) -> None:
        parameters = {
            'controller': 'ArticleCommentsController',
            'method': 'reportPost'
        }

        data = {
            'MIME Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'postId': str(post_id),
            'title': pagetitle,
            'namespace': '0',
            'token': self._get_token()
        }

        self.bot._post(self.bot._wikia_api_url, parameters, data)
    
    def _get_token(self) -> str:
        parameters = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }

        data = self.bot._get(self.bot._api_url, parameters)
        return data['query']['tokens']['csrftoken']
