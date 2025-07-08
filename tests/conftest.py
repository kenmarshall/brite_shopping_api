# tests/conftest.py
import sys
from unittest.mock import MagicMock

# Mock Google Maps Service (which requires API key at import time)
mock_google_maps_service_instance = MagicMock()
# If the app code does 'from app.services.google_maps_service import google_maps_service'
# then 'google_maps_service' is the object to mock within the module.
sys.modules['app.services.google_maps_service'] = MagicMock(google_maps_service=mock_google_maps_service_instance)

print("tests/conftest.py created and mocks applied.")
