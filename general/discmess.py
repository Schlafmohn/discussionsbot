import json
import copy
from typing import Optional, List, Dict, Any

class DiscussionsMessage:
    """
    Строит JSON-модель сообщения для Fandom Discussions, совместимую с ProseMirror.
    Поддерживает абзацы, жирный, курсив, ссылки, кодовые блоки и вложения (изображения, openGraph, упоминания).
    """

    def __init__(self):
        self._model: Dict[str, Any] = {
            "type": "doc",
            "content": []
        }

        self._attachments: Dict[str, List[Any]] = {
            "contentImages": [],
            "openGraphs": [],
            "atMentions": []
        }

        self._raw_text: str = ""
    
    @classmethod
    def from_existing(cls, raw_text: str, model: dict, attachments: dict) -> 'DiscussionsMessage':
        message = cls()
        message._raw_text = raw_text
        message._model = model
        message._attachments = attachments
        return message
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DiscussionsMessage':
        message = cls()
        message._raw_text = data.get("rawContent", "")
        message._model = data.get("jsonModel", {})
        message._attachments = data.get("attachments", {})
        return message
    
    @staticmethod
    def replace_in_message(raw_text: str, model: dict, attachments: dict, replacements: dict) -> dict:
        # делаем глубокую копию, чтобы не испортить оригинал
        model_copy = copy.deepcopy(model)
        attachments_copy = copy.deepcopy(attachments)
        model = DiscussionsMessage._replace_in_node(model_copy, replacements)[0]

        for var, rep in replacements.items():
            if "mention_id" in rep and "mention_text" in rep:
                # добавляем упоминание в attachments, если есть
                raw_text = raw_text.replace(var, f"@{rep['mention_text']}")
                attachments_copy.setdefault("atMentions", []).append({"id": rep["mention_id"]})
            else:
                # заменяем переменные в rawContent
                raw_text = raw_text.replace(var, rep.get("text", ""))

        return {"rawContent": raw_text, "jsonModel": model, "attachments": attachments_copy}
    
    @staticmethod
    def replace_in_message_from_dict(data: dict, replacements: dict) -> dict:
        return DiscussionsMessage.replace_in_message(data.get("rawContent", ""), data.get("jsonModel", {}), data.get("attachments", {}), replacements)
    
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
                    
                    # добавляем поддержку упоминания участников
                    if "mention_id" in rep and "mention_text" in rep:
                        nodes.append({
                            "type": "text",
                            "text": f"@{rep['mention_text']}",
                            "marks": [{"type": "mention", "attrs": {"userId": rep["mention_id"], "userName": rep["mention_text"], "href": None}}]
                        })

                    else:
                        # обычная текстовая замена
                        new_node = {"type": "text", "text": rep["text"]}
                        if rep.get("link"):
                            new_node["marks"] = node.get("marks", []) + [{"type": "link", "attrs": {"href": rep["link"]}}]
                        else:
                            new_node["marks"] = node.get("marks", [])
                        nodes.append(new_node)

                    if after:
                        nodes += DiscussionsMessage._replace_in_node({"type": "text", "text": after, "marks": node.get("marks", [])}, replacements)

                    return nodes
            
            # если ни одна переменная не найдена - вернуть узел как есть
            return [node]

        # если есть вложенный контент, рекурсивно пройтись по нему
        if "content" in node:
            node["content"] = [
                subnode
                for item in node["content"]
                for subnode in DiscussionsMessage._replace_in_node(item, replacements)
            ]

            return [node]
        return [node]

    def add_paragraph(self, text: Optional[str]=None, strong: bool=False, italic: bool=False, link: Optional[str]=None, marks: Optional[List[Dict[str, Any]]]=None) -> 'DiscussionsMessage':
        paragraph = {
            "type": "paragraph",
            "content": []
        }

        if text:
            paragraph["content"].append(self._format_text(text, strong=strong, italic=italic, link=link, marks=marks))
            self._raw_text += text + "\n"

        self._model["content"].append(paragraph)
        return self

    def add_code_block(self, text: Optional[str]=None) -> 'DiscussionsMessage':
        block = {
            "type": "code_block",
            "content": []
        }

        if text:
            block["content"].append({"type": "text", "text": text})
            self._raw_text += text + "\n"

        self._model["content"].append(block)
        return self

    def add_text_to_last(self, text: str, strong: bool=False, italic: bool=False, link: Optional[str]=None, marks: Optional[List[Dict[str, Any]]]=None) -> 'DiscussionsMessage':
        if not self._model["content"]:
            raise ValueError("Нет активного блока для добавления текста")

        block = self._model["content"][-1]
        if "content" not in block:
            block["content"] = []

        block["content"].append(self._format_text(text, strong=strong, italic=italic, link=link, marks=marks))
        self._raw_text += text
        return self
    
    def add_text_to_first(self, text: str, strong: bool=False, italic: bool=False, link: Optional[str]=None, marks: Optional[List[Dict[str, Any]]]=None) -> 'DiscussionsMessage':
        if not self._model["content"]:
            raise ValueError("Нет активного блока для добавления текста")

        block = self._model["content"][0]
        if "content" not in block:
            block["content"] = []

        block["content"].insert(0, self._format_text(text, strong=strong, italic=italic, link=link, marks=marks))
        self._raw_text = text + self._raw_text
        return self

    def add_mention(self, user_id: str, username: str) -> 'DiscussionsMessage': # todo: работает неправильно для Фэндома
        mention = {
            "type": "mention",
            "attrs": {
                "id": user_id,
                "text": "@{}".format(username)
            }
        }

        self._attachments["atMentions"].append({"id": user_id, "text": username})
        self._model["content"].append({"type": "paragraph", "content": [mention]})
        return self

    def add_image(self, url: str, width: int, height: int) -> 'DiscussionsMessage':
        image_data = {
            "imageUrl": url,
            "imageWidth": width,
            "imageHeight": height
        }

        self._attachments["contentImages"].append(image_data)
        self._model["content"].append({
            "type": "image",
            "attrs": {"id": len(self._attachments["contentImages"]) - 1}
        })

        return self

    def add_open_graph(self, url: str, site_name: str, title: str, description: str) -> 'DiscussionsMessage':
        if ".fandom.com/" not in url:
            return self

        graph = {
            "siteName": site_name,
            "title": title,
            "description": description,
            "type": "article",
            "url": url,
            "originalUrl": url
        }

        self._attachments["openGraphs"].append(graph)
        self._model["content"].append({
            "type": "openGraphs",
            "attrs": {
                "id": len(self._attachments["openGraphs"]) - 1,
                "url": url,
                "wasAddedWithInlineLink": True
            }
        })

        return self

    def build_model(self) -> Dict[str, Any]:
        return self._model

    def build_raw_model(self) -> str:
        return json.dumps(self._model)

    def build_attachments(self) -> Dict[str, List[Any]]:
        return self._attachments

    def build_raw_attachments(self) -> str:
        return json.dumps(self._attachments)

    def build_raw_text(self) -> str:
        return self._raw_text.strip()

    @staticmethod
    def _make_marks(strong: bool=False, italic: bool=False, link: Optional[str]=None) -> List[Dict[str, Any]]:
        marks: List[Dict[str, Any]] = []

        if strong:
            marks.append({"type": "strong"})

        if italic:
            marks.append({"type": "em"})

        if link:
            marks.append({"type": "link", "attrs": {"href": link}})
        return marks

    def _format_text(self, text: str, strong: bool=False, italic: bool=False, link: Optional[str]=None, marks: Optional[List[Dict[str, Any]]]=None) -> Dict[str, Any]:
        node: Dict[str, Any] = {"type": "text", "text": text}
        node_marks = marks if marks is not None else self._make_marks(strong, italic, link)

        if node_marks:
            node["marks"] = node_marks
        return node
