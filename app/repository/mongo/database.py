import os
import sys
from datetime import datetime
from typing import List

from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from models.user import User, InsertUser
from models.message import Message, PostMessage

from repository.mongo.utils import filter_by_id

sys.stdout.flush()

mongo_client: AsyncIOMotorClient = None


async def connect_mongo_messenger_database():
    global mongo_client
    mongo_messenger_uri = os.getenv('MONGO_MESSENGER_URI')
    mongo_messenger_db = os.getenv('MONGO_MESSENGER_DB')
    mongo_users_collection = os.getenv('MONGO_USERS_COLLECTION')
    mongo_messages_collection = os.getenv('MONGO_MESSAGES_COLLECTION')

    try:
        mongo_client = AsyncIOMotorClient(mongo_messenger_uri)
        await mongo_client.server_info()
        print(f'Connected to mongo with uri {mongo_messenger_uri}')

        # создать базу данных, если еще нет
        if mongo_messenger_db not in await mongo_client.list_database_names():
            await mongo_client.get_database(mongo_messenger_db).create_collection(mongo_users_collection)
            await mongo_client.get_database(mongo_messenger_db).create_collection(mongo_messages_collection)

            mongo_users_collection = mongo_client.get_database(
                mongo_messenger_db).get_collection(mongo_users_collection)
            mongo_messages_collection = mongo_client.get_database(
                mongo_messenger_db).get_collection(mongo_messages_collection)

            print(f'Database {mongo_messenger_db} created successfully!')

            return True

    except Exception as ex:
        print(f'Can\'t connect to mongo: {ex}')

        return False


async def close_mongo_messenger_database():
    global mongo_client
    if mongo_client is None:
        return
    mongo_client.close()


class MongoMessengerDatabase():
    def __init__(self):
        mongo_messenger_db = os.getenv('MONGO_MESSENGER_DB')
        mongo_users_collection = os.getenv('MONGO_USERS_COLLECTION')
        mongo_messages_collection = os.getenv('MONGO_MESSAGES_COLLECTION')

        self._mongo_users_collection = mongo_client.get_database(
            mongo_messenger_db).get_collection(mongo_users_collection)
        self._mongo_messages_collection = mongo_client.get_database(
            mongo_messenger_db).get_collection(mongo_messages_collection)

    async def __del__(self):
        await self.close_connection()

    async def create_user(self, user: InsertUser) -> str:
        insert_result = await self._mongo_users_collection.insert_one(dict(user))
        return str(insert_result.inserted_id)

    async def get_user_by_id(self, user_id: str) -> User:
        user = await self._mongo_users_collection.find_one(filter_by_id(user_id))
        return User.Map(user)

    async def add_message(self, message: PostMessage) -> str:
        insert_result = await self._mongo_messages_collection.insert_one(dict(message))
        return str(insert_result.inserted_id)

    async def get_message_by_id(self, message_id: str) -> Message:
        message = await self._mongo_messages_collection.find_one(filter_by_id(message_id))
        return Message.Map(message)

    async def get_chat_history(self, user_id: str, companion_id: str, date_offset: datetime = None, limit: int = 10) -> List[Message]:
        if date_offset is None:
            cursor = self._mongo_messages_collection.find({"$or": [{"sender_id": user_id, "receiver_id": companion_id},
                                                                               {"sender_id": companion_id, "receiver_id": user_id}]}).limit(limit).sort("post_date")
        else:
            cursor = self._mongo_messages_collection.find({"$or": [{"sender_id": user_id, "receiver_id": companion_id},
                                                                               {"sender_id": companion_id, "receiver_id": user_id}],
                                                                       "post_date": {"$lt": date_offset.isoformat()}}).limit(limit).sort("post_date")
        chat_history = []
        async for message in cursor:
            chat_history.append(Message.Map(message))

        return chat_history

    async def get_recent_users(self, user_id: str, date_offset: datetime = None, limit=10) -> List[str]:
        if date_offset is None:
            pipeline = [{"$match": {"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}}]
        else:
            pipeline = [{"$match": {"$and": [{"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}, {"post_date": {"$lt": date_offset.isoformat()}}]}}]
        pipeline += [
            {"$project": {"post_date": True, "dialoge_members": {"$setUnion": [["$sender_id"], ["$receiver_id"]]}}},
            {"$sort": {"dialoge_members": 1}},
            {"$group": {"_id": "$dialoge_members", "last_post_date": {"$max": "$post_date"}}},
            {"$sort": {"last_post_date": -1}},
            {"$limit": limit}
        ]

        recent_users = []
        async for recent_post in self._mongo_messages_collection.aggregate(pipeline):
            print(recent_post)
            for dialoge_member in recent_post["_id"]:
                if dialoge_member != user_id:
                    recent_users.append(dialoge_member)
            break

        return recent_users

    @staticmethod
    def get_instance():
        return MongoMessengerDatabase()
