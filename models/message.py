from datetime import datetime

from typing import Any

from pydantic import BaseModel

class MessageContent(BaseModel):
    text_content: str

class RawMessage(BaseModel):
    sender_id: str
    receiver_id: str
    content: MessageContent

    def __iter__(self):
        data = {}
        for key, value in self.__dict__.items():
            try:
                yield (key, dict(value))
            except Exception:
                yield (key, value)

class PostMessage(RawMessage):
    post_date: datetime

class Message(PostMessage):
    id: str

    @classmethod
    def Map(cls, message: Any):
        return cls(id=str(message['_id']),
                   sender_id=message['sender_id'],
                   receiver_id=message['receiver_id'],
                   content=MessageContent(text_content=message['content']['text_content']),
                   post_date=message['post_date'])