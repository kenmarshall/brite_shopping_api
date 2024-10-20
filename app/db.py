from pymongo import MongoClient


def init_db(configs, flask_env):
    mongo_configs = configs[f"mongo:{flask_env}"]
    client = MongoClient(mongo_configs["MONGO_URI"], uuidRepresentation="standard")
    return client.brite_shopping_db
