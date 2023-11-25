import os
import sys
from datetime import datetime
from typing import List

from fastapi import APIRouter, status, Depends
from starlette.responses import Response
from bson import ObjectId

from models.user import User, InsertUser
from models.message import Message, MessageContent, PostMessage, RawMessage

from repository.mongo.database import MongoMessengerDatabase
from repository.elasticsearch.database import ElasticsearchMessengerDatabase

from pymemcache import HashClient

from repository.cache.memcache import get_memcached_user_client, get_memcached_message_client, get_memcached_chat_history_client, get_memcached_recent_users_client

sys.stdout.flush()

router = APIRouter()


@router.post("/users")
async def create_user(name: str, username: str, 
                      messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance),
                      search_db: ElasticsearchMessengerDatabase = Depends(ElasticsearchMessengerDatabase.get_instance)):
    user = InsertUser(name=name, username=username,
                      creation_date=datetime.utcnow())
    user_id = await messenger_db.create_user(user)
    await search_db.create_user(user_id, user)
    return user_id


@router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(user_id: str, 
                         messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance),
                         memcached_user_client: HashClient = Depends(get_memcached_user_client)):
    if not ObjectId.is_valid(user_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    user = memcached_user_client.get(user_id)
    if user is not None:
        print('using cached user data')
        return user
    
    user = await messenger_db.get_user_by_id(user_id)
    if user is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    memcached_user_client.add(user_id, user, int(os.getenv('MEMCACHED_MESSENGER_USER_EXPIRE')))
    
    return user


@router.get("/users", response_model=List[User])
async def find_user_by_username(pattern: str,
                                search_db: ElasticsearchMessengerDatabase = Depends(ElasticsearchMessengerDatabase.get_instance)):
    return await search_db.get_by_username(pattern)


@router.post("/users/{user_id}/chats/{receiver_id}")
async def send_message(user_id: str, receiver_id: str, content: MessageContent, 
                       messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance),
                       search_db: ElasticsearchMessengerDatabase = Depends(ElasticsearchMessengerDatabase.get_instance)):
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(receiver_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    message = PostMessage(sender_id=user_id, receiver_id=receiver_id,
                          content=content, post_date=datetime.utcnow())
    message_id = await messenger_db.add_message(message)
    await search_db.create_message(message_id, message)
    return message_id


@router.get("/users/{user_id}/chats/{companion_id}")
async def get_chat_history(user_id: str, companion_id: str, date_offset: datetime = None, 
                           messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance),
                           memcached_chat_history_client: HashClient = Depends(get_memcached_chat_history_client),
                           memcached_message_client: HashClient = Depends(get_memcached_message_client)):
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(companion_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    if date_offset is not None:
        chat_history = memcached_chat_history_client.get(date_offset.isoformat())
        if chat_history is not None:
            print('using cached chat history data')
            return chat_history
    
    chat_history = await messenger_db.get_chat_history(user_id, companion_id=companion_id, date_offset=date_offset)
    if chat_history is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    for message in chat_history:
        memcached_message_client.add(message.id, message, int(os.getenv('MEMCACHED_MESSENGER_MESSAGE_EXPIRE')))

    if date_offset is None:
        cached_date_offset = datetime.utcnow().isoformat()
        memcached_chat_history_client.add(cached_date_offset, chat_history, int(os.getenv('MEMCACHED_MESSENGER_CHAT_HISTORY_EXPIRE')))
        return chat_history, {'cached_date_offset': cached_date_offset}
    else:
        memcached_chat_history_client.add(date_offset.isoformat(), chat_history, int(os.getenv('MEMCACHED_MESSENGER_CHAT_HISTORY_EXPIRE')))

    return chat_history


@router.get("/users/{user_id}/chats/{companion_id}/search", response_model=List[Message])
async def find_message(pattern: str, user_id: str, companion_id: str,
                       search_db: ElasticsearchMessengerDatabase = Depends(ElasticsearchMessengerDatabase.get_instance)):
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(companion_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    return await search_db.find_message(user_id, companion_id, pattern)


@router.get("/users/{user_id}/chats")
async def get_recent_users(user_id: str, date_offset: datetime = None,
                           messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance),
                           memcached_recent_users_client: MongoMessengerDatabase = Depends(get_memcached_recent_users_client),
                           memcached_user_client: MongoMessengerDatabase = Depends(get_memcached_user_client)):
    if not ObjectId.is_valid(user_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    recent_users = None
    if date_offset is not None:
        recent_users = memcached_recent_users_client.get(date_offset.isoformat())
    if recent_users is not None:
        print('using cached recent users data')
        return recent_users
    
    recent_users = await messenger_db.get_recent_users(user_id, date_offset)
    if recent_users is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    if date_offset is None:
        cached_date_offset = datetime.utcnow().isoformat()
        memcached_recent_users_client.add(cached_date_offset, recent_users, int(os.getenv('MEMCACHED_MESSENGER_RECENT_USERS_EXPIRE')))
        return recent_users, {'cached_date_offset': cached_date_offset}
    else:
        memcached_recent_users_client.add(date_offset.isoformat(), recent_users, int(os.getenv('MEMCACHED_MESSENGER_RECENT_USERS_EXPIRE')))
    
    return recent_users


@router.get("/messages/{message_id}", response_model=Message)
async def get_message_by_id(message_id: str, 
                            messenger_db: MongoMessengerDatabase = Depends(MongoMessengerDatabase.get_instance),
                            memcached_message_client: MongoMessengerDatabase = Depends(get_memcached_message_client)):
    if not ObjectId.is_valid(message_id):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    message = memcached_message_client.get(message_id)
    if message is not None:
        print('using cached message data')
        return message

    message = await messenger_db.get_message_by_id(message_id)
    if message is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    memcached_message_client.add(message_id, message, int(os.getenv('MEMCACHED_MESSENGER_MESSAGE_EXPIRE')))
    
    return message