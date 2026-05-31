import json
import os
import uuid
from typing import Optional, List

TOPICS = ['cuisine', 'shopping', 'tourism', 'worklife']
CONTENT_TYPES = ['vocabulary', 'dialogue', 'listening']


class ContentService:
    def __init__(self, content_file: str):
        self.content_file = content_file
        self.content = {}
        self.load_content()

    def load_content(self):
        if os.path.exists(self.content_file):
            try:
                with open(self.content_file, 'r', encoding='utf-8') as f:
                    self.content = json.load(f)
                print(f"Loaded practice content: {self.content_file}")
            except Exception as e:
                print(f"Failed to load content: {e}")
                self.content = self._empty_structure()
        else:
            self.content = self._empty_structure()
            self.save_content()

    def _empty_structure(self):
        return {topic: {ct: [] for ct in CONTENT_TYPES} for topic in TOPICS}

    def save_content(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.content_file), exist_ok=True)
            with open(self.content_file, 'w', encoding='utf-8') as f:
                json.dump(self.content, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save content: {e}")
            return False

    def get_items(self, topic: str, content_type: str) -> List[dict]:
        return list(self.content.get(topic, {}).get(content_type, []))

    def get_item(self, topic: str, content_type: str, item_id: str) -> Optional[dict]:
        for item in self.get_items(topic, content_type):
            if item['id'] == item_id:
                return item
        return None

    def add_item(self, topic: str, content_type: str, data: dict) -> Optional[dict]:
        if topic not in TOPICS or content_type not in CONTENT_TYPES:
            return None
        prefix = content_type[:3]
        item = {'id': f'{prefix}_{uuid.uuid4().hex[:8]}', **data}
        self.content.setdefault(topic, {}).setdefault(content_type, []).append(item)
        self.save_content()
        return item

    def update_item(self, topic: str, content_type: str, item_id: str, data: dict) -> Optional[dict]:
        items = self.content.get(topic, {}).get(content_type, [])
        for i, item in enumerate(items):
            if item['id'] == item_id:
                items[i] = {'id': item_id, **data}
                self.save_content()
                return items[i]
        return None

    def delete_item(self, topic: str, content_type: str, item_id: str) -> bool:
        items = self.content.get(topic, {}).get(content_type, [])
        for i, item in enumerate(items):
            if item['id'] == item_id:
                items.pop(i)
                self.save_content()
                return True
        return False

    def get_stats(self, topic: str) -> dict:
        return {
            ct: len(self.get_items(topic, ct))
            for ct in CONTENT_TYPES
        }
