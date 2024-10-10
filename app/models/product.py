import uuid

class ProductModel:
  def __init__(self, collection):
     self.collection = collection
  def get_one(self, id):
    return self.collection.find_one({"_id  ": id})
  def get_all(self):
    return self.collection.find()
  def add(self, data):
      # - TODO: add data validation
      data['_id'] = uuid.uuid4()
      self.collection.insert_one(data)
      