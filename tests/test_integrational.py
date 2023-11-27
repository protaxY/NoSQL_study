import requests
import urllib.parse
import json

from bson import ObjectId

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def test_ok(test_name):
    print(f"{test_name} - {bcolors.OKGREEN}OK{bcolors.ENDC}")

def test_fail(test_name):
    return f"\n{test_name} - {bcolors.FAIL}FAIL{bcolors.ENDC}"

def create_user(name, user_name):
    api_url = "http://localhost/messenger/users?"
    params = {'name': name, "username": user_name}

    request = api_url + urllib.parse.urlencode(params)

    print(f"request: {test_name}\n", request)
    response = requests.post(request)

    return response.json()

# Перед запуском этого файла,
# необходимо поднять инфраструктуру, используя команду docker-compose up в корне проекта.

# creating user
test_name = "Create user"
name = "anton"
user_name = "protaxY"

main_user_id = create_user(name, user_name)

assert ObjectId.is_valid(main_user_id), f"User id {main_user_id} is not a mongo ObjectID\nIt is type {type(main_user_id)}{test_fail(test_name)}"
test_ok(test_name)



# check user by id
test_name = "Check user by id"
api_url = f"http://localhost/messenger/users/{main_user_id}"

payload = {}
headers = {
  'accept': 'application/json'
}

response = requests.request("GET", api_url, headers=headers, data=payload)

assert response.status_code == 200, f"Cannot get user by ID{test_fail(test_name)}"
test_ok(test_name)



# get user by username
test_name = "get user by username"

api_url = "http://localhost/messenger/users?"
params = {'pattern': user_name}
request = api_url + urllib.parse.urlencode(params)

print(f"request: {test_name}\n", request)
response = requests.get(request)

assert response.status_code == 200, f"Status not OK{test_fail(test_name)}"
test_ok(test_name)
print(json.loads(response.text))


# send message
test_name = "send message"

# create another user
another_user_id = create_user("matvey", "whitedog")
assert ObjectId.is_valid(another_user_id), f"Cannot create another user{test_fail(test_name)}"

url = f"http://localhost/messenger/users/{another_user_id}/chats/{main_user_id}"

text_to_send = "Hello, anton!"
payload = json.dumps({
  "text_content": text_to_send
})
headers = {
  'accept': 'application/json',
  'Content-Type': 'application/json'
}

print(url)

response = requests.request("POST", url, headers=headers, data=payload)
message_id = response.json()

assert ObjectId.is_valid(message_id), f"User id {message_id} is not a mongo ObjectID\nIt is type {type(message_id)}{test_fail(test_name)}"
test_ok(test_name)


# get message by id
test_name = "get message by id"
api_url = f"http://localhost/messenger/messages/{message_id}"

payload = {}
headers = {
  'accept': 'application/json'
}

response = requests.request("GET", api_url, headers=headers, data=payload)

assert response.status_code == 200, f"Cannot get message by ID{test_fail(test_name)}"
test_ok(test_name)



# get history
test_name = "get history"
api_url = f"http://localhost/messenger/users/{main_user_id}/chats/{another_user_id}"

payload = {}
headers = {
  'accept': 'application/json'
}

response = requests.request("GET", api_url, headers=headers, data=payload)

assert response.status_code == 200, f"Response is not OK{test_fail(test_name)}"

response_json = json.loads(response.text)

print(response_json)
assert response_json[0][0]["content"]["text_content"] == text_to_send, f"Text not equal {text_to_send}\n{response_json}{test_fail(test_name)}"
test_ok(test_name)




# message by pattern
test_name = "message by pattern"

api_url = f"http://localhost/messenger/users/{another_user_id}/chats/{main_user_id}/search?"
params = {'pattern': text_to_send}
request = api_url + urllib.parse.urlencode(params)

print(f"request: {test_name}\n", request)

payload = {}
headers = {
  'accept': 'application/json'
}

response = requests.request("GET", request, headers=headers, data=payload)

assert response.status_code == 200, f"Response is not OK{test_fail(test_name)}"
response_json = json.loads(response.text)

print(len(response_json))
if len(response_json) == 0:
    assert response_json["id"] == message_id, f"Message id is not equal {message_id}\n{response_json}{test_fail(test_name)}"
else:
    assert response_json[0]["id"] == message_id, f"Message id is not equal {message_id}\n{response_json}{test_fail(test_name)}"
test_ok(test_name)



# get recent user
test_name = "get recent user"

api_url = f"http://localhost/messenger/users/{main_user_id}/chats"

print(f"request: {test_name}\n", api_url)

payload = {}
headers = {
  'accept': 'application/json'
}

response = requests.request("GET", api_url, headers=headers, data=payload)

assert response.status_code == 200, f"Response is not OK{test_fail(test_name)}"
test_ok(test_name)