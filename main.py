from dotenv import load_dotenv
from fastapi import FastAPI

from api.router import router
from repository.mongo_database import connect_mongo_messenger_database, close_mongo_messenger_database

load_dotenv()

app = FastAPI()

app.include_router(router, prefix="/messenger")
app.add_event_handler("startup", connect_mongo_messenger_database)
app.add_event_handler("shutdown", close_mongo_messenger_database)
