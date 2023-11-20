from typing import Any

from bson import ObjectId

from models.user import User
from models.message import Message

def filter_by_id(id: str) -> dict:
    return {'_id': ObjectId(id)}
