from pydantic import BaseModel

class Message(BaseModel):
    id: str
    from_id: str
    to_id: str
    # timestamp: 
    text_content: str
    images_content: str