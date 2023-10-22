from pydantic import BaseModel

from bson import ObjectId

class User(BaseModel):
    id: ObjectId
    name: str
    username: str
    # profile_picture: 

class InsertUser(BaseModel):
    username: str
    @property
    def name(self):
        return self.username
