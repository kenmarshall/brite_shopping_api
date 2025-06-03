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

## Deploying to Render

To deploy this application to Render, follow these steps:

1.  **Create a new Web Service on Render.**
2.  **Connect your Git repository.**
3.  **Set the Build Command:** `pip install -r requirements.txt`
4.  **Set the Start Command:** `gunicorn run:app`
5.  **Configure environment variables** as needed (e.g., `FLASK_ENV=production`, database URLs, API keys).
6.  **Deploy!**

Render will automatically detect the `Procfile` and use the `web` process type with the Gunicorn command.

## Memory Profiling (Development)

This project uses the `memory-profiler` library to help identify memory usage patterns and potential leaks during development.

### Enabling Profiling
To enable memory profiling for the `create_app` function:
1.  Ensure the `FLASK_ENV` environment variable is set to `development`.
2.  Set the `ENABLE_MEMORY_PROFILING` environment variable to `true`.

You can set these in your `.env` file or export them in your shell:
```bash
export FLASK_ENV=development
export ENABLE_MEMORY_PROFILING=true
```

### Running with Profiling
Once the environment variables are set, run the application as usual:
```bash
python run.py
```
The Flask development server will start, and if the conditions for profiling are met, the `memory-profiler` will be active for the decorated functions (currently `create_app`). The profiling output is typically sent to standard error when the application process terminates or when the profiler is explicitly instructed to dump statistics.

### Interpreting the Output
The profiler output for a function includes several columns:
-   **Line #**: The line number in the file.
-   **Mem usage**: Total memory usage by the Python interpreter after this line has been executed.
-   **Increment**: The difference in memory usage from the previous line. This helps pinpoint lines that cause significant memory increases.
-   **Occurrences**: Number of times this line was executed (useful for loops).
-   **Line Contents**: The actual code from the line.

### Initial Findings for `create_app`
During an initial profiling run (Note: this run used a minimal set of dependencies to isolate Flask application startup), the `create_app` function (specifically, the internal `create_app_internal` function it wraps) showed the following characteristics:
-   **Initial Memory Usage**: Approximately 47.6 MiB when the function starts.
-   **Increment within function**: Negligible. The lines within `create_app_internal` (Flask app instantiation, API setup, blueprint registration) did not individually show significant memory increments. This suggests the base Flask application setup has a stable memory footprint at startup.

Example output snippet:
```
Filename: /app/app/__init__.py

Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
    13     47.6 MiB     47.6 MiB           1   def create_app_internal(flask_env):
    14     47.6 MiB      0.0 MiB           1       app = Flask(__name__)
    15     47.6 MiB      0.0 MiB           1       logger.info(f"Starting app in {flask_env} environment.")
    ...
    24     47.6 MiB      0.0 MiB           1       return app
```

### Limitations of Current Profiling
-   The initial findings mentioned above were gathered by running the application with a stripped-down set of dependencies (`requirements_minimal.txt`) to ensure the application could run in a resource-constrained environment and to focus on the core application's memory footprint. Profiling with full dependencies (including AI models and other services) may yield different results and is a recommended next step for comprehensive analysis.
-   Profiling is currently applied only to the `create_app` function. For more detailed analysis, specific endpoints or service methods might need to be decorated with `@profile`.
