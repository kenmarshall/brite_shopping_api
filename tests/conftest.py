# tests/conftest.py
import sys
from unittest.mock import MagicMock

# Mock problematic modules that might be imported by app code
# These mocks will be in place before pytest tries to collect/import test files in subdirectories.

# Mock Google Maps Service (which requires API key at import time)
mock_google_maps_service_instance = MagicMock()
# If the app code does 'from app.services.google_maps_service import google_maps_service'
# then 'google_maps_service' is the object to mock within the module.
sys.modules['app.services.google_maps_service'] = MagicMock(google_maps_service=mock_google_maps_service_instance)

# Mock AI Service (which might have heavy dependencies like sentence_transformers or faiss)
mock_ai_service_instance = MagicMock()
def mock_generate_embedding(text):
    # Return a fixed-length list of floats as a dummy embedding
    return [0.1] * 768 # Adjust dimension if known, otherwise a generic one
mock_ai_service_instance.generate_embedding = mock_generate_embedding
# Mock other methods of AIService if they are called during import or by other services
mock_ai_service_instance.search_similar = MagicMock(return_value=([], []))
# This mocks the 'ai_service' object if the app does 'from app.services.ai_service import ai_service'
sys.modules['app.services.ai_service'] = MagicMock(ai_service=mock_ai_service_instance)

# Mock faiss and sentence_transformers directly as they can be problematic
sys.modules['faiss'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()

print("tests/conftest.py created and mocks applied.")
