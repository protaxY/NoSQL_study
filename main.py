from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from api.router import router

from repository.mongo.database import connect_mongo_messenger_database, close_mongo_messenger_database
from repository.elasticsearch.database import connect_elastic_messenger_database, close_elasticsearch_connect

async def Startup():
    await connect_mongo_messenger_database()
    await connect_elastic_messenger_database()

async def Shutdown():
    await close_mongo_messenger_database()
    await close_elasticsearch_connect()

load_dotenv()

app = FastAPI()

app.include_router(router, prefix="/messenger")
app.add_event_handler("startup", connect_mongo_messenger_database)
app.add_event_handler("shutdown", close_mongo_messenger_database)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
