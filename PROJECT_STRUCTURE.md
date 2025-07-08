# Brite Shopping API - Project Structure

This document outlines the folder and file structure of the Brite Shopping API backend built with Flask, MongoDB (via PyMongo), and Google Maps integration.

## Project Root

```
.
├── app/
├── tests/
├── README.md
├── render.yaml
├── requirements.txt
├── requirements_no_faiss.txt
├── run.py
├── LICENSE
└── UI_INTEGRATION_GUIDE.md
```

### File Descriptions:

* **`README.md`**: Provides an overview of the project, including setup instructions, dependencies, and usage guidelines.
* **`render.yaml`**: Configuration file for deploying the Flask application to Render hosting service.
* **`requirements.txt`**: Lists all Python dependencies for the API.
* **`requirements_no_faiss.txt`**: Alternative dependencies list (same as requirements.txt after cleanup).
* **`run.py`**: Entry point script to run and initialize the Flask application.
* **`LICENSE`**: MIT license file.
* **`UI_INTEGRATION_GUIDE.md`**: Instructions for integrating the backend API with the frontend UI.

## Application Directory (`app`)

```
app/
├── __init__.py
├── db.py
├── models/
├── resources/
└── services/
```

* **`__init__.py`**: Initializes Flask app instance and registers routes and services.
* **`db.py`**: Handles connection setup and management for MongoDB.

### Models (`app/models`)

```
models/
├── product_model.py
├── product_price_model.py
└── store_model.py
```

* **`product_model.py`**: Defines schema and database interactions for product entities with basic CRUD operations.
* **`product_price_model.py`**: Manages price records for products linked to specific stores.
* **`store_model.py`**: Defines schema and methods for store entities, including locations and details.

### Resources (`app/resources`)

```
resources/
├── __init__.py
├── product_resource.py
├── product_price_resource.py
├── store_resource.py
└── store_search_resource.py
```

* **`product_resource.py`**: REST API endpoints for product CRUD operations.
* **`product_price_resource.py`**: API endpoints for managing product price data.
* **`store_resource.py`**: API endpoints for CRUD operations on stores.
* **`store_search_resource.py`**: API endpoints specifically for searching and finding stores (Google Places integration).

### Services (`app/services`)

```
services/
├── __init__.py
├── google_maps_service.py
└── logger_service.py
```

* **`google_maps_service.py`**: Integration with Google Maps APIs for location search and validation.
* **`logger_service.py`**: Custom logging utility to track events, errors, and operations.

## Tests Directory (`tests`)

```
tests/
├── __init__.py
├── conftest.py
├── models/
│   ├── __init__.py
│   ├── test_core_models.py
│   └── test_store_model.py
├── resources/
│   ├── __init__.py
│   ├── test_product_resource.py
│   └── test_store_search_resource.py
└── unit/
    └── test_product.py
```

* **`conftest.py`**: Fixtures and setup configurations for pytest.

### Model Tests (`tests/models`)

* **`test_core_models.py`**: Unit tests for product, store, and price models.
* **`test_store_model.py`**: Unit tests specifically for store model methods and validations.

### Resource Tests (`tests/resources`)

* **`test_product_resource.py`**: Integration tests for product API endpoints.
* **`test_store_search_resource.py`**: Tests for store search and location validation APIs.

## Key Features

- **Simple Product Management**: Basic CRUD operations for grocery products
- **Store Location Services**: Google Maps integration for finding and validating store locations
- **Price Comparison**: Track and compare prices across multiple stores
- **Clean Architecture**: Simplified, maintainable Flask API design
- **Comprehensive Testing**: Unit and integration tests for all components

## API Endpoints

### Products
- `GET /products` - List all products or search by name
- `GET /products/{id}` - Get specific product details  
- `POST /products` - Add new product with store and price info

### Stores
- `GET /stores` - Find stores by address or name
- `GET /stores/search` - Search for store locations

### Product Prices
- `GET /products/{id}/prices` - Get all prices for a product
- `POST /products/{id}/prices` - Add price for a product at a store

## Dependencies

The API uses a minimal set of dependencies focused on core functionality:

- **Flask & Flask-RESTful**: Web framework and REST API support
- **PyMongo**: MongoDB database integration
- **Google Maps**: Store location and geocoding services
- **Gunicorn**: WSGI server for production deployment

AI and machine learning functionality has been moved to the separate `brite-shopping-catalog-engine` project for better separation of concerns.
