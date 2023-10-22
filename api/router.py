from fastapi import APIRouter, status, Depends
from starlette.responses import Response
from bson import ObjectId

from models.user import User, InsertUser
from models.message import Message

from repository.mongo_database import MongoMessengerDatabase

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user_profile(user_id: str, messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance), response_model=User):
    if not ObjectId.is_valid(user_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    user = await messenger_db.get_user(user_id)
    if user is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return user

@router.get("/messages/{message_id}")
async def get_message(message_id: str, messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance), response_model=Message):
    if not ObjectId.is_valid(message_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    message = await messenger_db.get_message(message_id)
    if message is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return message