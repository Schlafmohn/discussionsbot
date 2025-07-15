from gendiscbot import discmess

def commands(self, post):
    if not post['pingDiscBot']:
        return
    
    if 'ping' in post['content'].lower():
        replyPostCommand = discmess.DiscussionsMessage()
        replyPostCommand.addText(post['user'] + ', pong!')

        self.myBot.createReplyMessageWalk(
            replyPostCommand,
            threadID=post['threadID'],
            userID=self.myBot.getBotUserID()
        )
