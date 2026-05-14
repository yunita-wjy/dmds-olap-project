import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))

try:
    # test koneksi
    client.admin.command('ping')
    print("Connected to MongoDB!")
except Exception as e:
    print("Connection failed:", e)

db = client[os.getenv("MONGO_DB")]
product_coll = db["product_catalog"]
orders_coll = db["order_recap"]

