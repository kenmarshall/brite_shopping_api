import uuid

# TODO: Need to add some pagination and filtering and indexing name


class ProductModel:
    def __init__(self, collection):
        self.collection = collection

    def get_one(self, product_id):
        product = self.collection.find_one({"_id": uuid.UUID(product_id)})
        return product

    def get_all(self):
        documents = self.collection.find()

        result = []
        for document in documents:
            document["_id"] = str(document["_id"])
            result.append(document)
        return result

    def add(self, data):
        # - TODO: add data validation
        data["_id"] = uuid.uuid4()
        self.collection.insert_one(data)
