from datetime import datetime
from typing import Any

from pydantic import BaseModel

class InsertUser(BaseModel):
    name: str
    username: str
    creation_date: datetime

    def __iter__(self):
        for key, value in self.__dict__.items():
            try:
                if isinstance(value, datetime): # сделано для работы кэша
                    yield (key, value.isoformat())
                else:
                    yield (key, dict(value))
            except Exception:
                yield (key, value)

class User(InsertUser):
    id: str
    # profile_picture:

    @classmethod
    def Map(cls, user: Any):
        return cls(id=str(user['_id']),
                   name=user['name'],
                   username=user['username'],
                   creation_date=datetime.fromisoformat(user['creation_date']))