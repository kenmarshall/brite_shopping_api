# Brite Shopping API

## Description
A Flask-RESTful API for managing products and searching for store locations. It utilizes AI-powered search for products and integrates with Google Maps for location finding. It allows users to compare product prices across locations. 

## Features
*   Search and retrieve products (GET by ID or name, POST for new products).
*   Update and delete products (PUT, DELETE endpoints exist but core logic may require review/completion).
*   Find store locations using Google Maps (search by address or name within an area).
*   AI-powered product search capabilities (leveraging sentence transformers and FAISS).

## Technologies Used
*   Python
*   Flask, Flask-RESTful
*   MongoDB (pymongo)
*   Google Maps API
*   Sentence Transformers & FAISS (for AI/search)
*   python-dotenv

## Setup and Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/pricemart-api.git # Replace with actual URL
    cd pricemart-api # Replace with actual folder name
    ```
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Set up environment variables:
    Create a `.env` file in the root directory. Essential variables include:
    ```env
    FLASK_ENV=development
    MONGO_URI="your_mongodb_connection_string_here" # e.g., mongodb://localhost:27017/pricemart
    GOOGLE_MAPS_API_KEY="your_google_maps_api_key_here"
    # If using specific AI models locally or other services, add their keys/configs here
    # E.g., FAISS_INDEX_PATH="models/faiss_product_index.idx"
    ```

## Running the Application
1.  Ensure your MongoDB instance is running and accessible.
2.  Start the Flask development server:
    ```bash
    python run.py
    ```

## API Endpoints

### Products
*   **`GET /products`**
    *   Description: Retrieves a list of all products or filters products by name.
    *   Query Parameters:
        *   `name` (optional): Filter products by name.
    *   Example: `GET /products?name=SuperWidget`
    *   Response: `200 OK` with a list of product objects.
*   **`GET /products/<product_id>`**
    *   Description: Retrieves a specific product by its ID.
    *   Example: `GET /products/12345`
    *   Response: `200 OK` with the product object.
*   **`POST /products`**
    *   Description: Adds a new product.
    *   Request Body: JSON object representing the product.
        ```json
        {
            "name": "New Product",
            "price": 19.99,
            "description": "A fantastic new product."
        }
        ```
    *   Response: `201 Created` with `{"status": "success"}`.
*   **`PUT /products/<product_id>`**
    *   Description: Updates an existing product by its ID. (Note: The core database update logic for this endpoint in `product_resource.py` appears to be commented out and will need implementation).
    *   Request Body: JSON object with fields to update.
    *   Response: `200 OK` with `{"status": "success"}`.
*   **`DELETE /products/<product_id>`**
    *   Description: Deletes a product by its ID. (Note: The core database deletion logic for this endpoint in `product_resource.py` appears to be commented out and will need implementation).
    *   Response: `200 OK` with `{"status": "success"}`.

### Locations
*   **`GET /locations`**
    *   Description: Finds store locations by address or by name within a specified area.
    *   Query Parameters (provide one of the following sets):
        1.  `address`: The address to search for.
            *   Example: `GET /locations?address=1600%20Amphitheatre%20Parkway,%20Mountain%20View,%20CA`
        2.  `name`, `location`, `radius` (optional):
            *   `name`: Name of the store/place.
            *   `location`: Textual description of the search area (e.g., "San Francisco, CA") or latitude,longitude coordinates (e.g., "37.7749,-122.4194").
            *   `radius` (optional): Search radius in meters (default is 5000).
            *   Example: `GET /locations?name=CoffeeShop&location=New%20York&radius=1000`
    *   Response: `200 OK` with `{"data": result}` containing location information. `400 Bad Request` if required parameters are missing.
