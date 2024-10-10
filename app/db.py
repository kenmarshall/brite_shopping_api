import configparser
import os

from pymongo import MongoClient

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("config.ini")))


def init_db():
    client = MongoClient(config["DEV"]["MONGO_URI"], uuidRepresentation="standard")
    return client.brite_shopping_db
