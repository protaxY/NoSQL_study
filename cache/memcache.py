import os
import sys
from datetime import datetime

from pymemcache import HashClient

from cache.serializer import JsonSerializer


sys.stdout.flush()

memcached_user_client: HashClient = None
memcached_message_client: HashClient = None
memcached_chat_history_client: HashClient = None
memcached_recent_users_client: HashClient = None

def connect_messenger_memcached():
    global memcached_user_client
    global memcached_message_client
    global memcached_chat_history_client
    global memcached_recent_users_client

    memcached_user_uri = os.getenv('MEMCACHED_MESSENGER_USER_URI')
    memcached_message_uri = os.getenv('MEMCACHED_MESSENGER_MESSAGE_URI')
    memcached_chat_history_uri = os.getenv('MEMCACHED_MESSENGER_CHAT_HISTORY_URI')
    memcached_recent_users_uri = os.getenv('MEMCACHED_MESSENGER_RECENT_USERS_URI')

    memcached_uris = [memcached_user_uri,
                      memcached_message_uri,
                      memcached_chat_history_uri,
                      memcached_recent_users_uri]

    memcached_clients = [None for _ in range(4)]

    for i, (memcached_client, memcached_uri) in enumerate(zip(memcached_clients, memcached_uris)):
        try:
            memcached_clients[i] = HashClient(memcached_uri.split(','), serde=JsonSerializer())
            print(f'Connected to user memcached with uri {memcached_uri}')
        except Exception as ex:
            print(f'Cant connect to user memcached: {ex}')

    map_client_array(memcached_clients)


def close_memcached_connect():
    global memcached_user_client
    global memcached_message_client
    global memcached_chat_history_client
    global memcached_recent_users_client

    memcached_clients = [memcached_user_client,
                         memcached_message_client,
                         memcached_chat_history_client,
                         memcached_recent_users_client]

    for memcached_client in memcached_clients:
        if memcached_client is not None:
            memcached_client.close()

def map_client_array(memcached_clients):
    global memcached_user_client
    global memcached_message_client
    global memcached_chat_history_client
    global memcached_recent_users_client

    memcached_user_client = memcached_clients[0]
    memcached_message_client = memcached_clients[1]
    memcached_chat_history_client = memcached_clients[2]
    memcached_recent_users_client = memcached_clients[3]

# def datetime_to_string(date_offset: datetime | None):
#     if date_offset is None:
#         key = str(datetime.utcnow()).replace(' ', '_')
#     else:
#         key = str(date_offset).replace(' ', '_')
#     return key

def get_memcached_user_client():
    return memcached_user_client
def get_memcached_message_client():
    return memcached_message_client
def get_memcached_chat_history_client():
    return memcached_chat_history_client
def get_memcached_recent_users_client():
    return memcached_recent_users_client