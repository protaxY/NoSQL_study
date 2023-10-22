from pydantic import BaseModel

from bson import ObjectId

class User(BaseModel):
    id: str
    name: str
    username: str
    
    @staticmethod
    def map_mongo_user(user):
        if user is None:
            return None
        
        return User(id=str(user['_id']),
                    name=user['name'],
                    username=user['username'])

class InsertUser(BaseModel):
    username: str
    name: str
#     # @property
#     # def name(self):
#     #     return self.username
