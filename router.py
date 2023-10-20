from fastapi import APIRouter

from user import User

router = APIRouter()

# @router.get("/messages/")
# async def get_messages(sender_id: ):

# @router.get("/messages/")
# async def send_messages(sender_id: ):

@router.get("/user/{user_id}")
async def get_user_profile(user_id, response_model=User):
    