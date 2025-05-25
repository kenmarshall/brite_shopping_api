import unittest
import json
from unittest.mock import patch, MagicMock

from app import create_app
from app.models.store_model import StoreModel # Assuming StoreModel has an id attribute

class TestStoreResourcePost(unittest.TestCase):

    def setUp(self):
        """Set up test variables."""
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Tear down test variables."""
        self.app_context.pop()

    @patch('app.resources.store_resource.StoreModel.get_or_create')
    def test_create_new_store_success(self, mock_get_or_create):
        """Test successfully creating a new store (201)."""
        mock_store_instance = MagicMock(spec=StoreModel)
        mock_store_instance.id = 1
        mock_store_instance.name = "Test Store"
        
        mock_get_or_create.return_value = (mock_store_instance, True) # True for created

        response = self.client.post('/stores', 
                                     data=json.dumps({"name": "Test Store"}),
                                     content_type='application/json')
        
        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['message'], "Store created.")
        mock_get_or_create.assert_called_once_with(name="Test Store")

    @patch('app.resources.store_resource.StoreModel.get_or_create')
    def test_get_existing_store_success(self, mock_get_or_create):
        """Test successfully retrieving an existing store (200)."""
        mock_store_instance = MagicMock(spec=StoreModel)
        mock_store_instance.id = 2
        mock_store_instance.name = "Existing Store"

        mock_get_or_create.return_value = (mock_store_instance, False) # False for not created (already exists)

        response = self.client.post('/stores',
                                     data=json.dumps({"name": "Existing Store"}),
                                     content_type='application/json')
        
        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], 2)
        self.assertEqual(data['message'], "Store already exists.")
        mock_get_or_create.assert_called_once_with(name="Existing Store")

    def test_create_store_missing_name_failure(self):
        """Test creating a store with missing name (400)."""
        response = self.client.post('/stores',
                                     data=json.dumps({}), # Empty data
                                     content_type='application/json')
        
        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], "Store name is required.")

    def test_create_store_empty_json_failure(self):
        """Test creating a store with empty JSON (400)."""
        response = self.client.post('/stores',
                                     data=json.dumps(None), 
                                     content_type='application/json')
        
        data = json.loads(response.data.decode())
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], "Store name is required.")


if __name__ == '__main__':
    unittest.main()
