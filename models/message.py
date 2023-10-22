from pydantic import BaseModel

from bson import ObjectId

class Message(BaseModel):
    id: str
    from_id: str
    to_id: str
    # timestamp: 
    text_content: str
    
    @staticmethod
    def map_mongo_message(message):
        if message is None:
            return None
        
        return Message(id=str(message['_id']),
                       from_id=str(message['from_id']),
                       to_id=str(message['to_id']),
                       text_content=message['text_content'])