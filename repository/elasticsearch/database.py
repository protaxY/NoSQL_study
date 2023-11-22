import os
import sys
from typing import List

from elasticsearch import AsyncElasticsearch
from models.message import Message, MessageContent, PostMessage

from models.user import InsertUser, User

sys.stdout.flush()

elasticsearch_client: AsyncElasticsearch = None

async def connect_elastic_messenger_database():
    global elasticsearch_client
    elasticsearch_messenger_uri = os.getenv('ELASTICSEARCH_MESSANGER_URI')
    try:
        elasticsearch_client = AsyncElasticsearch(elasticsearch_messenger_uri)
        await elasticsearch_client.info()
        print(f'Connected to elasticsearch with uri {elasticsearch_messenger_uri}')
    except Exception as ex:
        print(f'Cant connect to elasticsearch: {ex}')

async def close_elasticsearch_connect():
    global elasticsearch_client
    if elasticsearch_client is None:
        return
    await elasticsearch_client.close()

class ElasticsearchMessengerDatabase():
    def __init__(self):       
        self._elasticsearch_users_index = os.getenv('ELASTICSEARCH_USERS_INDEX')
        self._elasticsearch_messages_index = os.getenv('ELASTICSEARCH_MESSAGES_INDEX')
        
    async def get_by_username(self, username: str) -> List[User]:
        query = {"match": {"username": {"query": username}}}
        response = await elasticsearch_client.search(index=self._elasticsearch_users_index,
                                                     query=query,
                                                     filter_path=['hits.hits._id', 'hits.hits._source'])
        if 'hits' not in response.body:
            return []
        response_users = response.body['hits']['hits']
        
        users = list(map(lambda user: User(id=user['_id'], 
                                           name=user['_source']['name'], 
                                           username=user['_source']['username'],
                                           creation_date=user['_source']['creation_date']), response_users))
        return users
    
    async def get_by_name(self, name: str) -> List[User]:
        query = {"match": {"name": {"query": name}}}
        response = await elasticsearch_client.search(index=self._elasticsearch_users_index,
                                                     query=query,
                                                     filter_path=['hits.hits._id', 'hits.hits._source'])
        if 'hits' not in response.body:
            return []
        response_users = response.body['hits']['hits']
        users = list(map(lambda user: User(id=user['_id'], 
                                           name=user['_source']['name'], 
                                           username=user['_source']['username'],
                                           creation_date=user['_source']['creation_date']), response_users))
        return users
    
    async def find_message(self, user_id: str, companion_id: str, pattern: str) -> List[Message]:
        query = {'bool': {'must': [
            {'bool': {'should': [
                {'bool': {'must': [{"match": {"sender_id": {"query": user_id}}},
                    {"match": {"receiver_id": {"query": companion_id}}}]}}, # либо user_id - отправитель, а companion_id - получатель
                {'bool': {'must': [{"match": {"sender_id": {"query": companion_id}}},
                    {"match": {"receiver_id": {"query": user_id}}}]}} # либо наоборот
            ]}},
            {"match": {"content.text_content": {"query": pattern}}} # найти слова в сообщении
        ]}}
        response = await elasticsearch_client.search(index=self._elasticsearch_messages_index,
                                                     query=query,
                                                     filter_path=['hits.hits._id', 'hits.hits._source'])
        if 'hits' not in response.body:
            return []
        response_messages = response.body['hits']['hits']
        messages = list(map(lambda message: Message(id=message['_id'], 
                                           sender_id=message['_source']['sender_id'], 
                                           receiver_id=message['_source']['receiver_id'],
                                           content=MessageContent(text_content=message['_source']['content']['text_content']),
                                           post_date=message['_source']['post_date']), response_messages))
        return messages
    
    async def create_user(self, user_id: str, user: InsertUser):
        await elasticsearch_client.create(index=self._elasticsearch_users_index, id=user_id, document=dict(user))

    async def update_user(self, user_id: str, user: InsertUser):
        await elasticsearch_client.update(index=self._elasticsearch_index, id=user_id, doc=dict(user))

    async def delete_user(self, user_id: str):
        await elasticsearch_client.delete(index=self._elasticsearch_index, id=user_id)
    
    async def create_message(self, message_id: str, message: PostMessage) -> str:
        await elasticsearch_client.create(index=self._elasticsearch_messages_index, id=message_id, document=dict(message))

    @staticmethod
    def get_instance():
        return ElasticsearchMessengerDatabase()
