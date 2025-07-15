import json

from gendiscbot import discmess

from datetime import datetime, timezone, timedelta

def autogreeting(self, post):
    if post['userID'] in self.settings['famousUsers']:
        # если участник уже есть в кэше, его нет смысла проверять
        return
        
    if post['type'] in ['EDIT', 'NEW', 'LOG', 'CATEGORIZE']:
        dataPostsUser = self.myBot.getUserContributions(userID=post['userID'])
    else:
        dataPostsUser = self.myBot.getUserProfileActivity(userID=post['userID'])
        
    if (datetime.now(timezone.utc) - dataPostsUser[0]['timestamp']) <= timedelta(hours=24):
        # если участник присоединился к вики более, чем 24 часа, то его добавляют в кэш
        self.settings['famousUsers'].append(post['userID'])
        return
        
    # после всех проверок убеждаемся, что участник - новый, составляем приветственное сообщение и отправляем
    with open('configs/autogreeting.json', 'r') as file:
        dataAutogreeting = json.loads(file.read())

    postAutogreeting = discmess.DiscussionsMessage()
    for item in dataAutogreeting['jsonModel']['content']:
        if item['type'] == 'paragraph':
            postAutogreeting.addParagraph()
            helpCreatePostAutogreeting(self, post, postAutogreeting, item)
            
        if item['type'] == 'code_block':
            postAutogreeting.addCodeBlock()
        
        if item['type'] == 'bulletList':
            postAutogreeting.addBulletList().addListItem()
            helpCreatePostAutogreeting(self, post, postAutogreeting, item)
            
        if item['type'] == 'orderedList':
            postAutogreeting.addOrderedList().addListItem()
            helpCreatePostAutogreeting(self, post, postAutogreeting, item)

    self.myBot.createThreadMessageWalk(postAutogreeting, dataAutogreeting['title'], userID=post['userID'])

def helpCreatePostAutogreeting(self, post, postAutogreeting, itemDataAutogreeting):
    for ktem in itemDataAutogreeting['content']:
        isMarkStrong = False
        isMarkItalic = False
        isMarkLink = None

        if '$USERNAME' in ktem['text']:
            ktem['text'] = ktem['text'].replace('$USERNAME', post['user'])
            
        if '$WIKINAME' in ktem['text']:
            ktem['text'] = ktem['text'].replace('$WIKINAME', self.myBot.getWikiName())
            
        if '$PAGENAME' in ktem['text']:
            # весь этот сложный цикл был сделан ради масштабируемости
            # конкретно - ради того, чтобы всегда была ссылка на вики-страницу
            helpCreatePostAutogreetingPagename(self, post, postAutogreeting, ktem)

            # ввиду того, что мы изменили само содержание `content`, то нижний код будет некорректно работать
            continue

        for mark in ktem.get('marks', []):
            if mark.get('type') == 'strong':
                isMarkStrong = True
                        
            if mark.get('type') == 'em':
                isMarkItalic = True
                        
            if mark.get('type') == 'link':
                isMarkLink = mark['attrs']

        postAutogreeting.addText(ktem['text'],
            strong=isMarkStrong,
            italic=isMarkItalic,
            link=isMarkLink
        )
    
def helpCreatePostAutogreetingPagename(self, post, postAutogreeting, ktemHelperAutogreeting):
    isMarkStrong = False
    isMarkItalic = False

    # разделяем строку на до и после - ссылка должна быть только на сам $PAGENAME
    ktemHelperAutogreeting['text'] = ktemHelperAutogreeting['text'].split('$PAGENAME')

    for mark in ktemHelperAutogreeting.get('marks', []):
        if mark.get('type') == 'strong':
            isMarkStrong = True
                        
        if mark.get('type') == 'em':
            isMarkItalic = True

    # сначала добавляем текст до $PAGENAME, сохраняя форматирование, заданное администраторами
    postAutogreeting.addText(ktemHelperAutogreeting['text'][0],
        strong=isMarkStrong,
        italic=isMarkItalic
    )

    # теперь добавляем само название $PAGENAME вместе с ссылкой, по прежнему сохраняя форматирование
    postAutogreeting.addText(self.myBot.getPageName(post),
        strong=isMarkStrong,
        italic=isMarkItalic,
        link=self.myBot.getPageLink(post)
    )

    # ну и теперь добавляем текст после $PAGENAME, также сохраняя форматирование
    postAutogreeting.addText(ktemHelperAutogreeting['text'][1],
        strong=isMarkStrong,
        italic=isMarkItalic
    )
