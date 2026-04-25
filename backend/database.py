import os
from motor.motor_asyncio import AsyncIOMotorClient

# Connect to MongoDB container. Use localhost if running FastAPI natively, 
# or use the service name 'mongodb' if running FastAPI inside docker.
MONGO_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_URL)
db = client.nyusearch_db

async def get_db():
    return db
