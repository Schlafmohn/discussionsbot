import re
import json

import autogreeting

from datetime import datetime

from gendiscbot import discmess

def commands(self, post):
    normalContent = re.sub(r'\s+', ' ', post['content'].strip()) # нормализуем пробелы

    pattern = fr'@?{re.escape(self.myBot.getBotUserName())}\s?,\s?(.*)'
    match = re.match(pattern, normalContent) # вытаскиваем имя бота и команду

    if not match:
        # имя бота нет, значит, нет и команды, пропускаем сообщение
        return
    
    fullCommand = match.group(1) # вытаскиваем только команду (см. паттерн)
    
    with open('languages/{}.json'.format(self.myBot.getWikiLang()), 'r') as file:
        dataReplyPost = json.loads(file.read())
    
    lowerFullCommand = fullCommand.lower()
    replyPostCommand = discmess.DiscussionsMessage()

    if 'ping' in lowerFullCommand or 'pong' in lowerFullCommand:
        ping(self, post, replyPostCommand, dataReplyPost)
    
    elif 'autogreeting on' in lowerFullCommand or 'autogreeting enable' in lowerFullCommand:
        autogreetingEnable(self, post, replyPostCommand, dataReplyPost)
    
    elif 'autogreeting off' in lowerFullCommand or 'autogreeting disable' in lowerFullCommand:
        autogreetingDisable(self, post, replyPostCommand, dataReplyPost)
    
    elif 'autogreeting title' in lowerFullCommand:
        autogreetingTitle(self, post, fullCommand, replyPostCommand, dataReplyPost)
    
    elif 'autogreeting message' in lowerFullCommand:
        pass
    
    elif 'report on' in lowerFullCommand or 'report enable' in lowerFullCommand:
        pass
    
    elif 'report off' in lowerFullCommand or 'report disable' in lowerFullCommand:
        pass
    
    elif 'warn add' in lowerFullCommand:
        warnAdd(self, post, fullCommand, replyPostCommand, dataReplyPost)
    
    elif 'warn list' in lowerFullCommand:
        warnList(self, post, fullCommand, replyPostCommand, dataReplyPost)
    
    elif 'warn delete' in lowerFullCommand:
        pass
    
    elif 'random' in lowerFullCommand:
        pass
    
    else:
        # неверная команда
        return
    
    self.myBot.createReplyMessageWall(
        replyPostCommand,
        threadID=post['threadID'],
        userID=self.myBot.getBotUserID()
    )
    
    if 'update autopost' in post['content'].lower():
        # обновление всего сообщения приветствия новых участников

        with open('configs/autogreeting.json', 'r') as file:
            dataAutogreeting = json.loads(file.read())

        with open('configs/autogreeting.json', 'w') as file:
            # нужно подправить `jsonModel`, потому что в нем первый `paragraph` относится к команде `update autopost`
            jsonModel = json.loads(post['jsonModel'])
            jsonModel['content'].pop(0)

            dataAutogreeting['rawContent'] = post['content'].split('update autopost ')[1]
            dataAutogreeting['jsonModel'] = jsonModel
            dataAutogreeting['attachments'] = post['attachments']

            print(dataAutogreeting, '\n\n\n', dataAutogreeting['jsonModel'])

            file.write(json.dumps(dataAutogreeting))
        
        replyPostCommand = discmess.DiscussionsMessage()
        replyPostCommand.addText(dataReplyPost['UPDATE AUTOPOST'].replace('$USERNAME', post['user']))

        self.myBot.createReplyMessageWall(
            replyPostCommand,
            threadID=post['threadID'],
            userID=self.myBot.getBotUserID()
        )

        return

def ping(self, post, replyPostCommand, dataReplyPost):        
    replyPostCommand.addText(post['user'], strong=True).addText(', привет! Я, ').addText(self.myBot.getBotUserName(), strong=True)
    replyPostCommand.addText(', – бот обсуждений, написанный абсолютно с нуля участником Зубенко Михаил Петрович. Если у тебя будут какие-то вопросы, лучше обращайся к нему. Держи даже ')
    replyPostCommand.addText('ссылку', link='https://warriors-cats.fandom.com/ru/wiki/Стена_обсуждения:Зубенко_Михаил_Петрович').addText('. Мне нет никакого смысла писать, я не обладаю даже встроенной функцией от Chat GPT 🏓')

def autogreetingEnable(self, post, replyPostCommand, dataReplyPost):
    with open('configs/autogreeting.json', 'r') as file:
        dataAutogreeting = json.loads(file.read())
        
    with open('configs/autogreeting.json', 'w') as file:
        dataAutogreeting['status'] = True
        dataAutogreeting = json.loads(file.read())
    
    replyPostCommand.addText(post['user'], strong=True).addText(', автоприветствия успешно включены ✅')
    replyPostCommand.addParagraph('Теперь каждому новому участнику будут автоматически отправляться приветственное сообщение! Чтобы сделать его индивидуальнее, вы можете настроить:')
    replyPostCommand.addBulletList('autogreeting title: [новый заголовок]', strong=True).addText(' — изменить заголовок')
    replyPostCommand.addListItem('autogreeting message: [новое сообщение]', strong=True).addText(' — изменить текст приветствия')

    replyPostCommand.addParagraph('📌 В тексте сообщения можно использовать следующие переменные:')
    replyPostCommand.addBulletList('$USERNAME', strong=True).addText(' — имя нового участника')
    replyPostCommand.addListItem('$WIKINAME', strong=True).addText(' — название вашей вики')
    replyPostCommand.addListItem('$PAGENAME', strong=True).addText(' — название страницы или темы, где участник впервые проявил активность')

    replyPostCommand.addParagraph('🔧 Текущие настройки автоприветствия:')
    replyPostCommand.addParagraph('Заголовок:', strong=True).addText(dataAutogreeting['title'])
    replyPostCommand.addParagraph('Сообщение:', strong=True).addText(dataAutogreeting['jsonModel'])

    replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
    replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))

def autogreetingDisable(self, post, replyPostCommand, dataReplyPost):
    with open('configs/autogreeting.json', 'r') as file:
        dataAutogreeting = json.loads(file.read())
        
    with open('configs/autogreeting.json', 'w') as file:
        dataAutogreeting['status'] = False
        dataAutogreeting = json.loads(file.read())
    
    replyPostCommand.addText(post['user'], strong=True).addText(', автоприветствие новых участников выключено. Я больше не буду автоматически приветствовать пользователей при их первом действии. Если вы захотите снова включить эту функцию, используйте команду: ')
    replyPostCommand.addText('autogreeting enable', strong=True).addText('.')

    replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
    replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))

def autogreetingTitle(self, post, fullCommand, replyPostCommand, dataReplyPost):
    newTitle = fullCommand[20:] # `autogreeting title: ` – 20 символов

    with open('configs/autogreeting.json', 'r') as file:
        dataAutogreeting = json.loads(file.read())
        
    with open('configs/autogreeting.json', 'w') as file:
        dataAutogreeting['title'] = newTitle
        file.write(json.dumps(dataAutogreeting))
    
    replyPostCommand.addText(post['user'], strong=True).addText(', заголовок автоприветствия успешно обновлен 🎉')
    replyPostCommand.addParagraph('Чтобы изменить содержание самого автоматического сообщения новых участников, воспользуйтесь командой: ')
    replyPostCommand.addText('autogreeting message: [новое сообщение]', strong=True).addText('.')

    replyPostCommand.addParagraph('📌 В тексте приветствия вы можете использовать специальные переменные:')
    replyPostCommand.addBulletList('$USERNAME', strong=True).addText(' — имя нового участника')
    replyPostCommand.addListItem('$WIKINAME', strong=True).addText(' — название вашей вики')
    replyPostCommand.addListItem('$PAGENAME', strong=True).addText(' — название страницы или темы, где участник впервые проявил активность')

    replyPostCommand.addParagraph('🔧 Текущие настройки автоприветствия:')
    replyPostCommand.addParagraph('Заголовок:', strong=True).addText(dataAutogreeting['title'])
    replyPostCommand.addParagraph('Сообщение:', strong=True).addText(dataAutogreeting['jsonModel'])

    replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
    replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))

def warnAdd(self, post, fullCommand, replyPostCommand, dataReplyPost):
    pattern = r'warn add\s?@?(.+?)(?:\s?:\s?)(.+)'
    match = re.match(pattern, fullCommand)

    if not match:
        # неверная команда
        return
    
    username = match.group(1).replace('_', ' ') # вытаскиваем имя нарушителя (см. паттерн)
    reason = match.group(2) # вытаскиваем причину нарушения

    with open('configs/warns.json', 'r') as file:
        dataWarns = json.loads(file.read())
    
    if not username in dataWarns:
        # проверяем, а есть ли этот участник вообще на вики
        if not self.myBot.existsUserID(username):
            # неверная команда
            return
        
        dataWarns[username] = []
    
    dataWarns[username].append({
        'moderator': post['user'],
        'reason': reason,
        'timestamp': datetime.strptime(post['timestamp'], '%d.%m.%Y %H:%M:%S')
    })

    replyPostCommand.addText(post['user'], strong=True).addText(', предупреждение успешно добавлено ⚠️')
    replyPostCommand.addParagraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
    replyPostCommand.addText('warn delete @username: 1 2', strong=True).addText(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

    replyPostCommand.addParagraph('📋 Текущий список предупреждений для участника ' + username + ':')
    replyPostCommand.addBulletList()

    for warn in dataWarns[username]:
        replyPostCommand.addListItem(dataWarns[username]['timestamp'] + ' от ' + dataWarns[username]['moderator'] + '. Причина: ' + dataWarns[username]['reason'])

    replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
    replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))

def warnList(self, post, fullCommand, replyPostCommand, dataReplyPost):
    pattern = r'warn list\s?@?(.+)'
    match = re.match(pattern, fullCommand)

    if not match:
        # неверная команда
        return
    
    username = match.group(1).replace('_', ' ') # вытаскиваем имя нарушителя (см. паттерн)

    with open('configs/warns.json', 'r') as file:
        dataWarns = json.loads(file.read())
    
    if not username in dataWarns:
        # неверная команда
        return
    
    replyPostCommand.addText(post['user'], strong=True).addText(', список активных предупреждений, выданных этому участнику ⚠️')
    replyPostCommand.addBulletList()

    for warn in dataWarns[username]:
        replyPostCommand.addListItem(dataWarns[username]['timestamp'] + ' от ' + dataWarns[username]['moderator'] + '. Причина: ' + dataWarns[username]['reason'])

    replyPostCommand.addParagraph('Чтобы удалить одно или несколько предупреждений, используйте команду в формате: ')
    replyPostCommand.addText('warn delete @username: 1 2', strong=True).addText(' — где числа соответствуют номерам предупреждений, которые нужно удалить.')

    replyPostCommand.addParagraph('📚 Полный список команд: ').addText('команды бота', link='https://discbot.fandom.com/ru/wiki/Команды_бота')
    replyPostCommand.addText('. Не забудьте в начале упомянуть мое имя {} через запятую!'.format(self.myBot.getBotUserName()))
