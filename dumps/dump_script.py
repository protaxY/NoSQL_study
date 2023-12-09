import requests
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
from tqdm import tqdm
from pyspark.sql import SparkSession

from bson import ObjectId

DUMP_USERS_FILE_NAME = 'dumps/users_data_set.json'

async def create_user(name, user_name, user_creation_date):
    api_url = "http://localhost/messenger/users?"
    params = {'name': name, "username": user_name, "timestamp": user_creation_date}
    request = api_url + urllib.parse.urlencode(params)
    response = await requests.post(request)
    return response.json()

def send_message(text_to_send, from_user, to_user, post_date):
    url = f"http://localhost/messenger/users/{from_user}/chats/{to_user}"

    payload = json.dumps({
        "text_content": text_to_send,
        "timestamp": post_date,
    })
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    print(url)
    requests.request("POST", url, headers=headers, data=payload)

spark = SparkSession.builder \
  .appName("writeExample") \
  .master("spark://spark-master:<port>") \
  .config("spark.jars", "<mongo-spark-connector-JAR-file-name>") \
  .getOrCreate()

# подготовка пользователей
# users_tree = ET.parse('dumps/Users.xml')
# users_root = users_tree.getroot()
# users_data_set = dict()

# if os.path.isfile(DUMP_USERS_FILE_NAME):
#     print("file with users already exists. Trying to load users into dictionary...")
#     with open(DUMP_USERS_FILE_NAME, 'r') as f:
#         users_data_set = json.load(f)

# else :
#     print("Dump file do not exists. Creating new users...")
#     with tqdm(total=len(users_root)) as pbar:
#         for user in users_root:
#             user_id = user.get('AccountId')
#             creation_date = user.get('CreationDate')
#             user_name = user.get('DisplayName')
#             # pbar.write(f"Creating user {user_name}")
#             # mongo_db_user_id = create_user(user_name, user_name, creation_date)

#             users_data_set[user_id] = {"CreationDate": creation_date, "UserName": user_name}
#             pbar.update(1)
            

# with open(DUMP_USERS_FILE_NAME, 'w') as f:
#     print("saving users dump into json file...")
#     json.dump(users_data_set, f)