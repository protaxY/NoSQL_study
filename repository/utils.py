from bson import ObjectId

from models.user import User
from models.message import Message

def filter_by_id(id: str) -> dict:
    return {'_id': ObjectId(id)}

def map_message(message: Any) -> Message | None:
    if message is None:
        return None

    return Message(id=message['_id'], \
                   from_id=message['from_id'], \
                   to_id=message['to_id'], \
                   text_content=message['text_content'])

def map_user(user: Any) -> User:
    if user is None:
        return None
    
    return User(id=user['_id'], \
                name=user['name'], \
                username=user['username'])