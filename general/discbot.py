class DiscussionsBot:
    def __init__(self, username: str, password: str, wikilink: str):
        from .disccore import DiscussionsCore
        from .activity import DiscussionsActivity
        from .moderation import DiscussionsModeration

        self.core = DiscussionsCore(username, password, wikilink)
        self.activity = DiscussionsActivity(self.core)
        self.moderation = DiscussionsModeration(self.core, self.activity)
