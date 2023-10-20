from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    username: str
    # profile_picture: 

class InsertUser(BaseModel):
    username: str
    @property
    def name(self):
        return self.username
