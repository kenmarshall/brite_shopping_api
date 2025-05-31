# UI Integration Guide: Creating Products with Store and Price

This guide outlines the steps to integrate the UI with the backend for the new feature allowing users to specify a store and price when creating a product.

## 1. UI Modifications for Product Creation Form

The product creation form needs the following additions:

*   **Product Name:** (Existing field, likely) Text input for the product's name.
*   **Product Description:** (Optional, existing field, likely) Text area for product description.
*   **Store Search Query:** Text input where the user can type the name or address of the store.
*   **Store Search Results Display:** A way to display a list of store candidates returned by the backend (e.g., a dropdown, a list). Each candidate should ideally show store name and address.
*   **Selected Store Display:** Once a store is selected, display its name and address clearly. This confirms the selection to the user.
*   **Price:** Number input for the product's price at the selected store.
*   **Currency:** (Optional) Text input or dropdown for currency (e.g., "USD", "JMD"). Defaults to "JMD" if not provided to the backend.

## 2. Fetching Store Information

When the user types in the "Store Search Query" field and initiates a search (e.g., on input change with debounce, or via a search button):

*   **API Call:** Make a `GET` request to the backend endpoint: `/stores/search`.
    *   If the user is searching by store name: `/stores/search?name=<user_query>`
    *   If the user is searching by address: `/stores/search?address=<user_query>`
    *   Example using `fetch` API:
        ```javascript
        // Assuming userQuery is the text from the store search input
        // and searchType is 'name' or 'address'
        let searchQueryParam = searchType === 'name' ? `name=${encodeURIComponent(userQuery)}` : `address=${encodeURIComponent(userQuery)}`;
        fetch(`/stores/search?${searchQueryParam}`)
            .then(response => {
                if (!response.ok) {
                    // Handle non-2xx responses (e.g., 400, 404, 500)
                    return response.json().then(err => Promise.reject(err));
                }
                return response.json();
            })
            .then(data => {
                // data should be like: {"stores": [storeObject1, storeObject2, ...]}
                // or an error message if the response was not ok initially but still JSON
                displayStoreCandidates(data.stores);
            })
            .catch(error => {
                console.error('Error fetching stores:', error);
                // Display an error message to the user, e.g., from error.message
                displaySearchError(error.message || 'Failed to fetch stores.');
            });
        ```

*   **Handling Response:**
    *   The backend will respond with a JSON object, typically:
        ```json
        {
            "stores": [
                {
                    "name": "Store Name 1",
                    "place_id": "google_place_id_1",
                    "address": "123 Main St, City",
                    "latitude": 34.0522,
                    "longitude": -118.2437
                    // ... other fields from Google Places if available
                },
                // ... more stores
            ]
        }
        ```
    *   If no stores are found, it might be an empty list `[]` with a 200 OK, or a 404 error with a message like `{"message": "No store found...", "stores": []}`. The UI should handle both.
*   **Displaying Candidates:** Show the list of `stores` to the user. For each store, display at least its `name` and `address`.
*   **User Selection:** When the user selects a store from the candidates, the UI must store all the details of the selected store, especially:
    *   `place_id` (critical for the backend)
    *   `name` (can be referred to as `store` in the final payload)
    *   `address`
    *   Any other relevant fields like `latitude`, `longitude` if needed for display or other UI features.

## 3. Submitting the New Product

Once the user has filled in the product name, selected a store, and entered the price:

*   **Construct JSON Payload:** Create a JSON object with the following structure:
    ```json
    {
        "product_data": {
            "name": "User's Product Name", // Required
            "description": "User's Product Description" // Optional
            // Any other product-specific fields
        },
        "store_info": {
            // These fields come from the store selected by the user from the /stores/search results
            "store": "Selected Store Name",         // Required by StoreModel if place_id doesn't uniquely identify
            "place_id": "selected_google_place_id", // Required by StoreModel
            "address": "Selected Store Address",    // Recommended
            "latitude": 12.345,                     // Optional
            "longitude": -67.890                    // Optional
            // Include any other details obtained from the store search result for completeness
        },
        "price": 123.45, // Required, must be a number
        "currency": "USD" // Optional, defaults to "JMD" on backend
    }
    ```
    *   **Important:** `store_info.place_id` is critical. `store_info.store` should be the name of the store.

*   **API Call:** Make a `POST` request to the `/products` endpoint with the JSON payload.
    ```javascript
    fetch('/products', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload) // payload is the object constructed above
    })
    .then(response => {
        if (!response.ok) {
            // Handle errors, e.g., 400 for validation, 500 for server error
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        // data should be like: {"message": "Product created successfully", "product_id": "...", "store_id": "..."}
        console.log('Product created:', data);
        // Handle success (e.g., show success message, redirect, clear form)
    })
    .catch(error => {
        console.error('Error creating product:', error);
        // Display an error message to the user from error.message
        displaySubmitError(error.message || 'Failed to create product.');
    });
    ```

## 4. Error Handling Notes

*   **Store Search (`GET /stores/search`):**
    *   `400 Bad Request`: If `name` or `address` query parameter is missing. Message: `{"message": "A 'name' or 'address' query parameter is required"}`.
    *   `400 Bad Request`: If Google Maps API key is invalid or other service-side input issue. Message from service.
    *   `404 Not Found`: If no stores are found for the query. Message: `{"message": "No store found...", "stores": []}`.
    *   `500 Internal Server Error`: For unexpected backend errors.
*   **Product Creation (`POST /products`):**
    *   `400 Bad Request`: For validation errors (e.g., missing product name, invalid price, missing `place_id`). The response will contain a specific error message: `{"message": "Specific error details"}`.
        *   `"Product data with name is required"`
        *   `"Store info is required"`
        *   `"Store place_id is required"`
        *   `"Price is required and must be a number"`
    *   `500 Internal Server Error`: For unexpected backend errors.

The UI should be prepared to handle these responses gracefully and provide appropriate feedback to the user.
