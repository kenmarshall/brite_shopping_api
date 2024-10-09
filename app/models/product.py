from app.db import mongo

class Product:
  def get(self, id):
    return mongo.db.products.find_one({"_id  ": id})