from fastapi import APIRouter, status, Depends
from starlette.responses import Response
from bson import ObjectId

from models.user import User, InsertUser
from models.message import Message

from repository.mongo_database import MongoMessengerDatabase

router = APIRouter()

@router.get("/users/{user_id}", response_model=User)
async def get_user_profile(user_id: str,
                           messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance)):
    if not ObjectId.is_valid(user_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    user = await messenger_db.get_user(user_id)
    if user is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return User.map_mongo_user(user)

@router.post("/users", response_model=str)
async def add_user_profile(insert_user: InsertUser,
                           messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance)):   
    inserted_id = await messenger_db.add_user(insert_user)    
    if inserted_id is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    return inserted_id

@router.get("/users")
async def get_users(n_users: int,
                    messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance)):
    users = messenger_db.get_users(n_users)
    return users

@router.get("/messages/{message_id}", response_model=Message)
async def get_message(message_id: str, messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance)):
    if not ObjectId.is_valid(message_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    message = await messenger_db.get_message(message_id)
    if message is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return message