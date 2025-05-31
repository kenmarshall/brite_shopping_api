import sys
import unittest
from unittest.mock import MagicMock, patch # Ensure patch is imported
from bson import ObjectId
from pymongo import ReturnDocument

# conftest.py should handle mocking app.services.google_maps_service, ai_service, faiss, sentence_transformers

from app.models.store_model import StoreModel
# No direct db import here, will be patched

class TestStoreModelGetOrCreate(unittest.TestCase):

    @patch('app.models.store_model.db') # Patch the db object used by StoreModel
    def test_get_or_create_new_store(self, mock_app_db):
        mock_stores_collection = MagicMock()
        mock_app_db.stores = mock_stores_collection # Make db.stores use this mock

        new_store_data = {"place_id": "place123", "store": "Test Store", "address": "123 Test St"}
        # data_for_set will be store_data excluding place_id, and None values (none here)
        expected_data_for_set = {"store": "Test Store", "address": "123 Test St"}

        expected_id = ObjectId()
        mock_stores_collection.find_one_and_update.return_value = {"_id": expected_id, **new_store_data}

        result_id = StoreModel.get_or_create(new_store_data)

        mock_stores_collection.find_one_and_update.assert_called_once_with(
            {"place_id": "place123"},
            {"$set": expected_data_for_set, "$setOnInsert": {"place_id": "place123"}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        self.assertEqual(result_id, expected_id)

    @patch('app.models.store_model.db')
    def test_get_or_create_updates_existing_store(self, mock_app_db):
        mock_stores_collection = MagicMock()
        mock_app_db.stores = mock_stores_collection

        existing_store_data = {"place_id": "place456", "store": "Updated Store Name", "address": "Updated Address"}
        expected_data_for_set = {"store": "Updated Store Name", "address": "Updated Address"}

        expected_id = ObjectId() # ID of the existing store
        # Simulate find_one_and_update finding and updating, returning the updated doc
        mock_stores_collection.find_one_and_update.return_value = {
            "_id": expected_id,
            "place_id": "place456", # from $setOnInsert or already there
            **expected_data_for_set    # from $set
        }

        result_id = StoreModel.get_or_create(existing_store_data)

        mock_stores_collection.find_one_and_update.assert_called_once_with(
            {"place_id": "place456"},
            {"$set": expected_data_for_set, "$setOnInsert": {"place_id": "place456"}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        self.assertEqual(result_id, expected_id)

    @patch('app.models.store_model.db')
    def test_get_or_create_no_place_id(self, mock_app_db):
        # This test doesn't need mock_stores_collection as it should fail before DB call
        store_data_no_place_id = {"store": "Test Store No Place ID"}
        with self.assertRaisesRegex(ValueError, "Store place_id is required"):
            StoreModel.get_or_create(store_data_no_place_id)
        mock_app_db.stores.find_one_and_update.assert_not_called()


    @patch('app.models.store_model.db')
    def test_get_or_create_no_store_name(self, mock_app_db):
        store_data_no_name = {"place_id": "place789"}
        with self.assertRaisesRegex(ValueError, "Store name .* required"): # Match updated error
            StoreModel.get_or_create(store_data_no_name)
        mock_app_db.stores.find_one_and_update.assert_not_called()

    @patch('app.models.store_model.db')
    def test_get_or_create_with_none_values_in_data(self, mock_app_db):
        mock_stores_collection = MagicMock()
        mock_app_db.stores = mock_stores_collection

        store_data_with_none = {"place_id": "place101", "store": "Store With None", "address": None, "link": "http://example.com"}
        # data_for_set should filter out 'address: None'
        expected_data_for_set = {"store": "Store With None", "link": "http://example.com"}
        
        expected_id = ObjectId()
        mock_stores_collection.find_one_and_update.return_value = {"_id": expected_id, "place_id": "place101", **expected_data_for_set}

        result_id = StoreModel.get_or_create(store_data_with_none)

        mock_stores_collection.find_one_and_update.assert_called_once_with(
            {"place_id": "place101"},
            {"$set": expected_data_for_set, "$setOnInsert": {"place_id": "place101"}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        self.assertEqual(result_id, expected_id)

if __name__ == '__main__':
    unittest.main()
