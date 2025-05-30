import sys
import unittest
from unittest.mock import MagicMock, patch
from bson import ObjectId
from pymongo import ReturnDocument

# Mock heavy dependencies before they are imported by app code
MOCK_MODULES = [
    "faiss",
    "sentence_transformers",
    "app.services.ai_service", # Mock the entire service
    "app.services.google_maps_service", 
    # Add other problematic modules here if they appear
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# Assuming app.models.store_model and app.db are discoverable in PYTHONPATH
# If not, adjustments to sys.path might be needed for a test runner
# For now, let's assume they are.
from app.models.store_model import StoreModel
# We don't import 'db' directly here, we'll mock the collection passed to StoreModel

class TestStoreModelGetOrCreate(unittest.TestCase):

    def setUp(self):
        self.mock_collection = MagicMock()
        self.store_model_instance = StoreModel(self.mock_collection)

    def test_get_or_create_new_store(self):
        new_store_data = {
            "place_id": "place123",
            "store": "Test Store",
            "address": "123 Test St",
            "latitude": 10.0,
            "longitude": 20.0
        }
        # Remove None values, as the method does
        clean_new_store_data = {k: v for k, v in new_store_data.items() if v is not None}

        expected_id = ObjectId()
        self.mock_collection.find_one_and_update.return_value = {
            "_id": expected_id,
            **clean_new_store_data
        }

        result_id = self.store_model_instance.get_or_create(new_store_data)

        self.mock_collection.find_one_and_update.assert_called_once_with(
            {"place_id": "place123"},
            {"$setOnInsert": clean_new_store_data},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        self.assertEqual(result_id, expected_id)

    def test_get_or_create_existing_store(self):
        existing_store_data = {
            "place_id": "place456",
            "store": "Existing Store",
            "address": "456 Old St",
        }
        # Remove None values
        clean_existing_store_data = {k:v for k,v in existing_store_data.items() if v is not None}


        expected_id = ObjectId()
        # Simulate that the store is found and returned
        self.mock_collection.find_one_and_update.return_value = {
            "_id": expected_id,
            "place_id": "place456", # Should already have this
            "store": "Existing Store",
            "address": "456 Old St",
            # Potentially other fields from when it was created
        }

        result_id = self.store_model_instance.get_or_create(existing_store_data)

        self.mock_collection.find_one_and_update.assert_called_once_with(
            {"place_id": "place456"},
            {"$setOnInsert": clean_existing_store_data}, # This data would be set if it were an insert
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        self.assertEqual(result_id, expected_id)
        # We don't need to assert $setOnInsert didn't change fields,
        # as find_one_and_update handles that. The key is it was called correctly.

    def test_get_or_create_no_place_id(self):
        store_data_no_place_id = {
            "store": "Test Store No Place ID"
        }
        with self.assertRaisesRegex(ValueError, "Store place_id is required"):
            self.store_model_instance.get_or_create(store_data_no_place_id)
        
        self.mock_collection.find_one_and_update.assert_not_called()

    def test_get_or_create_no_store_name(self):
        store_data_no_name = {
            "place_id": "place789"
            # Missing "store" (name)
        }
        with self.assertRaisesRegex(ValueError, "Store name is required"):
            self.store_model_instance.get_or_create(store_data_no_name)

        self.mock_collection.find_one_and_update.assert_not_called()

    def test_get_or_create_with_none_values_in_data(self):
        store_data_with_none = {
            "place_id": "place101",
            "store": "Store With None",
            "address": None, # This should be cleaned
            "latitude": 10.5
        }
        
        cleaned_data = {
            "place_id": "place101",
            "store": "Store With None",
            "latitude": 10.5
        }
        if "place_id" not in cleaned_data and store_data_with_none.get("place_id"): # logic from original code
             cleaned_data["place_id"] = store_data_with_none.get("place_id")


        expected_id = ObjectId()
        self.mock_collection.find_one_and_update.return_value = {"_id": expected_id, **cleaned_data}

        result_id = self.store_model_instance.get_or_create(store_data_with_none)

        self.mock_collection.find_one_and_update.assert_called_once_with(
            {"place_id": "place101"},
            {"$setOnInsert": cleaned_data},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        self.assertEqual(result_id, expected_id)

if __name__ == '__main__':
    unittest.main()
