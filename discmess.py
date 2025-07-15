import json

class DiscussionsMessage:
    def __init__(self, text=None, strong=False, italic=False, link=None):
        self.__rawContent = ''

        self.__jsonModel = {
            "type": "doc",
            "content": []
        }

        self.__attachments = {
            "contentImages": [],
            "openGraphs": [],
            "atMentions": []
        }

        self.addParagraph(text=text, strong=strong, italic=italic, link=None)
    
    def addParagraph(self, text=None, strong=False, italic=False, link=None):
        self.__jsonModel['content'].append({
            'type': 'paragraph',
            'content': []
        })

        if text:
            self.addText(text, strong=strong, italic=italic, link=None)

        return self
    
    def addCodeBlock(self, text=None):
        self.__jsonModel['content'].append({
            'type': 'code_block',
            'content': []
        })

        if text:
            self.addText(text)
        
        return self
    
    def addBulletList(self, text=None, strong=False, italic=False, link=None):
        self.__jsonModel['content'].append({
            'type': 'bulletList',
            'attrs': { 'createdWith': None },
            'content': []
        })

        self.addListItem(text=text, strong=strong, italic=italic, link=None)        
        return self
    
    def addOrderedList(self, text=None, strong=False, italic=False, link=None):
        self.__jsonModel['content'].append({
            'type': 'orderedList',
            'attrs': { 'createdWith': None },
            'content': []
        })

        self.addListItem(text=text, strong=strong, italic=italic, link=None)
        return self
    
    def addListItem(self, text=None, strong=False, italic=False, link=None):
        self.__jsonModel['content'][-1]['content'].append({
            'type': 'listItem',
            'content': [{
                'type': 'paragraph',
                'content': []
            }]
        })

        if text:
            self.addText(text=text, strong=strong, italic=italic, link=None)
        
        return self
    
    def addText(self, text, strong=False, italic=False, link=None):
        if self.__jsonModel['content'][-1]['type'] == 'paragraph':
            self.__jsonModel['content'][-1]['content'].append(self.__helpText(text, strong=strong, italic=italic, link=link))
        
        if self.__jsonModel['content'][-1]['type'] == 'code_block':
            self.__jsonModel['content'][-1]['content'].append(self.__helpText(text))
        
        if self.__jsonModel['content'][-1]['type'] == 'bulletList':
            self.__jsonModel['content'][-1]['content'][-1]['content'][-1]['content'].append(self.__helpText(text, strong=strong, italic=italic, link=link))
        
        if self.__jsonModel['content'][-1]['type'] == 'orderedList':
            self.__jsonModel['content'][-1]['content'][-1]['content'][-1]['content'].append(self.__helpText(text, strong=strong, italic=italic, link=link))

        return self
    
    def __helpText(self, text, strong=False, italic=False, link=None):
        self.__rawContent += text

        jsonModelHelpText = {
            'type': 'text',
            'marks': [],
            'text': text,
        }

        if strong:
            jsonModelHelpText['marks'].append({
                'type': 'strong'
            })
        
        if italic:
            jsonModelHelpText['marks'].append({
                'type': 'em'
            })
        
        if link:
            jsonModelHelpText['marks'].append({
                'type': 'link',
                'attrs': link,
                'title': None
            })
    
        return jsonModelHelpText
    
    def addImage(self, link, width=800, height=400):
        if not 'https://static.wikia.nocookie.net/' in link:
            return self
        
        helpImage = {
            'url': link,
            'width': width,
            'height': height
        }
        
        self.__attachments['contentImages'].append(helpImage)

        self.__jsonModel['content'].append({
            'type': 'image',
            'attrs': {
                'id': self.__attachments['contentImages'].index(helpImage)
            }
        })

        return self
    
    def addLinkImage(self, link, wikiname, title, description):
        if not '.fandom.com/' in link:
            return self
        
        helpLinkImage = {
            # 'imageHeight': imageHeight,
            # 'imageUrl': imageLink,
            # 'imageWidth': imageWidth,
            'siteName': wikiname,
            'title': title,
            'description': description,
            'type': 'article',
            'url': link,
            'originalUrl': link
        }
        
        self.__attachments['openGraphs'].append(helpLinkImage)

        self.__jsonModel['content'].append({
            'type': 'openGraphs',
            'attrs': {
                'id': self.__attachments['openGraphs'].index(helpLinkImage),
                'url': link,
                'wasAddedWithInlineLink': True
            }
        })

        return self

    def getRawContent(self):
        return self.__rawContent
    
    def getJSONModel(self):
        return json.dumps(self.__jsonModel)

    def getAttachments(self):
        return json.dumps(self.__attachments)
