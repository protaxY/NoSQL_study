import requests
import urllib.parse
import json
import xml.etree.ElementTree as ET
import os
from tqdm import tqdm
from pyspark.sql import SparkSession

from bson import ObjectId

DUMP_USERS_FILE_NAME = 'dumps/users_data_set.json'
DUMP_MSG_FILE_NAME = 'dumps/msg_data_set.json'



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

msg_tree = ET.parse('dumps/Posts.xml')
msg_root = msg_tree.getroot()
post_roots = dict()
msg_data_set = []

# first prepare post_roots
with tqdm(total=len(msg_root)) as pbar:
    for msg in msg_root:
        if msg.get("PostTypeId") == "1" and msg.get("OwnerUserId") != None:
           post_roots[msg.get("Id")] = msg.get("OwnerUserId") 
        pbar.update(1)

print("Creating new message data set...")
with tqdm(total=len(msg_root)) as pbar:
    for msg in msg_root:
        creation_date = msg.get('CreationDate')
        message_body = msg.get('Body')
        if msg.get("PostTypeId") == "1":
            # автор поста отправляет сообщение самому себе
            msg_data_set.append({
                "FromUser": msg.get("OwnerUserId"),
                "ToUser": msg.get("OwnerUserId"),
                "Message": message_body,
                "CreationDate": creation_date,
            })
        else:
            to_user = ""
            try:
                to_user = post_roots[msg.get("ParentId")]
            except KeyError:
                # пропускаем все сообщения, у которых неправильный родитель
                continue
            msg_data_set.append({
                "FromUser": msg.get("OwnerUserId"),
                "ToUser": to_user,
                "Message": message_body,
                "CreationDate": creation_date,
            })

        pbar.update(1)

with open(DUMP_MSG_FILE_NAME, 'w') as f:
    print("saving users dump into json file...")
    json.dump(msg_data_set, f)