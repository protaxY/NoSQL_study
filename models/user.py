from datetime import datetime
from typing import Any

from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    username: str
    creation_date: datetime
    # profile_picture:

    @classmethod
    def Map(cls, user: Any):
        return cls(id=str(user['_id']),
                   name=user['name'],
                   username=user['username'],
                   creation_date=user['creation_date'])


class InsertUser(BaseModel):
    name: str
    username: str
    creation_date: datetime