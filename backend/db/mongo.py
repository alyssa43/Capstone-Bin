from config import MONGO_URL
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()          # -> "chum_bucket" from the URL
requests_collection = db["captured_requests"]

def get_requests_collection():
    return requests_collection
