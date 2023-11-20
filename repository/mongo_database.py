import os
from datetime import datetime

from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from models.user import User, InsertUser
from models.message import Message, PostMessage

from repository.utils import filter_by_id

db_client: AsyncIOMotorClient = None


async def connect_mongo_messenger_database():
    print(os.getenv('MONGO_MESSENGER_URI'), flush=True)

    global db_client
    mongo_messenger_uri = os.getenv('MONGO_MESSENGER_URI')
    mongo_messenger_db = os.getenv('MONGO_MESSENGER_DB')
    mongo_users_collection = os.getenv('MONGO_USERS_COLLECTION')
    mongo_messages_collection = os.getenv('MONGO_MESSAGES_COLLECTION')

    try:
        db_client = AsyncIOMotorClient(mongo_messenger_uri)
        await db_client.server_info()
        print(f'Connected to mongo with uri {mongo_messenger_uri}', flush=True)

        # создать базу данных, если еще нет
        if mongo_messenger_db not in await db_client.list_database_names():
            await db_client.get_database(mongo_messenger_db).create_collection(mongo_users_collection)
            await db_client.get_database(mongo_messenger_db).create_collection(mongo_messages_collection)

            mongo_users_collection = db_client.get_database(
                mongo_messenger_db).get_collection(mongo_users_collection)
            mongo_messages_collection = db_client.get_database(
                mongo_messenger_db).get_collection(mongo_messages_collection)

            print(f'Database {mongo_messenger_db} created successfully!', flush=True)

            return True

    except Exception as ex:
        print(f'Can\'t connect to mongo: {ex}', flush=True)

        return False


async def close_mongo_messenger_database():
    global db_client
    if db_client is None:
        return
    db_client.close()


class MongoMessengerDatabase():
    def __init__(self):
        mongo_messenger_db = os.getenv('MONGO_MESSENGER_DB')
        mongo_users_collection = os.getenv('MONGO_USERS_COLLECTION')
        mongo_messages_collection = os.getenv('MONGO_MESSAGES_COLLECTION')

        self._mongo_users_collection = db_client.get_database(
            mongo_messenger_db).get_collection(mongo_users_collection)
        self._mongo_messages_collection = db_client.get_database(
            mongo_messenger_db).get_collection(mongo_messages_collection)

    async def __del__(self):
        await self.close_connection()

    async def create_user(self, user: InsertUser):
        insert_result = await self._mongo_users_collection.insert_one(dict(user))
        return insert_result

    async def get_user_by_id(self, user_id: str):
        user = await self._mongo_users_collection.find_one(filter_by_id(user_id))
        return user

    async def add_message(self, message: PostMessage):
        insert_result = await self._mongo_messages_collection.insert_one(dict(message))
        return insert_result

    async def get_message_by_id(self, message_id: str):
        message = await self._mongo_messages_collection.find_one(filter_by_id(message_id))
        return message

    async def get_chat_history(self, user_id: str, companion_id: str, date_offset: datetime = None, limit: int = 10):
        if not date_offset:
            cursor = self._mongo_messages_collection.find({"$or": [{"sender_id": user_id, "receiver_id": companion_id},
                                                                               {"sender_id": companion_id, "receiver_id": user_id}]}).limit(limit).sort("creation_date")
        else:
            cursor = self._mongo_messages_collection.find({"$or": [{"sender_id": user_id, "receiver_id": companion_id},
                                                                               {"sender_id": companion_id, "receiver_id": user_id}],
                                                                       "creation_date": {"$gt": date_offset}}).limit(limit).sort("creation_date")
        chat_history = []
        async for message in cursor:
            chat_history.append(message)

        return chat_history

    async def get_recent_users(self, user_id: str, date_offset: datetime = None, limit=10):
        if not date_offset:
            pipeline = [{"$match": {"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}}]
        else:
            pipeline = [{"$match": {"$and": [{"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}, {"post_date": {"$gt": date_offset}}]}}]
        pipeline += [
            {"$project": {"post_date": True, "dialoge_members": {"$setUnion": [["$sender_id"], ["$receiver_id"]]}}},
            {"$sort": {"dialoge_members": 1}},
            {"$group": {"_id": "$dialoge_members", "last_post_date": {"$max": "$post_date"}}},
            {"$sort": {"last_post_date": -1}},
            {"$limit": limit}
        ]

        recent_users = []
        async for recent_post in self._mongo_messages_collection.aggregate(pipeline):
            print(recent_post, flush=True)
            for dialoge_member in recent_post["_id"]:
                if dialoge_member != user_id:
                    recent_users.append(dialoge_member)
            break

        return recent_users

    @staticmethod
    def get_instance():
        return MongoMessengerDatabase()
