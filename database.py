import os

from motor.motor_asyncio import AsyncIOMotorClient

from models.user import User, InsertUser
from models.message import Message

class MongoMessengerDatabase():
    def __init__(self):
        self._db_client = None

    async def create_and_connect(self):
        try:
            self._db_client = AsyncIOMotorClient(self._mongo_uri)
            await self._db_client.server_info()
            print(f'Connected to mongo with uri {self._mongo_uri}')

            # создать базу данных, если еще нет
            if self._mongo_messenger_db not in await self._db_client.list_database_names():
                await self._db_client.get_database(self._mongo_messenger_db).create_collection(os.getenv('MONGO_USERS_COLLECTION'))
                await self._db_client.get_database(self._mongo_messenger_db).create_collection(os.getenv('MONGO_MESSAGES_COLLECTION'))

                self._mongo_users_collection = self._db_client.get_database(os.getenv('MONGO_MESSENGER_DB')).get_collection(os.getenv('MONGO_USERS_COLLECTION'))
                self._mongo_messages_collection = self._db_client.get_database(os.getenv('MONGO_MESSENGER_DB')).get_collection(os.getenv('MONGO_MESSAGES_COLLECTION'))

                print(f'Database {self._mongo_messenger_db} created successfully!')

                return True

        except Exception as ex:
            print(f'Can\'t connect to mongo: {ex}')
            
            return False

    async def close_connection(self):
        if self._db_client is None:
            return
        await self._db_client.close()

    async def __del__(self):
        self.close_connection()

    async def add_user(self, user: InsertUser):
        insert_result = await self._mongo_users_collection.insert_one(dict(user))
        return str(insert_result)
    
    async def add_message(self, message: Message):
        insert_result = await self._mongo_messages_collection.insert_one(dict(message))
        return str(insert_result)
    
    # async def get_messages(self, ):
