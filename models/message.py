from pydantic import BaseModel

from bson import ObjectId

class Message(BaseModel):
    id: ObjectId
    from_id: ObjectId
    to_id: ObjectId
    text_content: str