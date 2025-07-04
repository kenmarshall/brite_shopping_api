import os
import time
from openai import OpenAI, RateLimitError, APIError
from app.services.logger_service import logger

class ProductCategorizer:
    """
    Handles product categorization using an LLM (OpenAI's GPT models).
    """
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"): # Using 3.5-turbo as a default for cost/speed
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables.")
            raise ValueError("OPENAI_API_KEY is required for ProductCategorizer.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.logger = logger

    def categorize_product(self, product_name: str, brand: str = None, description: str = None, max_retries: int = 3) -> list[str]:
        """
        Categorizes a product into logical grocery store categories using an LLM.

        :param product_name: The name of the product.
        :param brand: The brand of the product (optional).
        :param description: A description of the product (optional).
        :param max_retries: Maximum number of retries for the API call.
        :return: A list of up to 5 category strings, or an empty list if categorization fails.
        """
        if not product_name:
            self.logger.warning("Product name is empty, cannot categorize.")
            return []

        prompt_parts = [f"Product Name: {product_name}"]
        if brand:
            prompt_parts.append(f"Brand: {brand}")
        if description:
            prompt_parts.append(f"Description: {description}")

        product_info = "\n".join(prompt_parts)

        system_prompt = (
            "You are a grocery product categorization expert. "
            "Based on the provided product information, identify up to 5 relevant grocery store categories. "
            "Return the categories as a comma-separated list. "
            "Example categories: 'Dairy, Eggs & Cheese', 'Beverages', 'Snacks', 'Pantry Staples', 'Fruits & Vegetables', "
            "'Meat & Seafood', 'Frozen Foods', 'Bakery', 'Household & Cleaning', 'Personal Care & Health'."
            "Be specific but also consider broader categories if applicable. "
            "If the product is 'Coca-Cola Original Taste', categories could be: 'Beverages, Soda, Soft Drinks'."
            "If the product is 'Kraft Macaroni & Cheese Dinner Original', categories could be: 'Pantry Staples, Pasta & Grains, Boxed Meals'."
            "If the product is 'Tide PODS Laundry Detergent Pacs', categories could be: 'Household & Cleaning, Laundry Supplies'."
        )

        user_prompt = f"Product Information:\n{product_info}\n\nCategories (comma-separated list):"

        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempting to categorize product: '{product_name}' (Attempt {attempt + 1}/{max_retries})")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2, # Lower temperature for more deterministic categories
                    max_tokens=100
                )

                categories_str = response.choices[0].message.content.strip()
                if not categories_str:
                    self.logger.warning(f"LLM returned empty string for categories for product: {product_name}")
                    return []

                categories = [cat.strip() for cat in categories_str.split(',') if cat.strip()]

                # Ensure up to 5 categories
                categories = categories[:5]

                self.logger.info(f"Successfully categorized '{product_name}' into: {categories}")
                return categories

            except RateLimitError as e:
                self.logger.warning(f"Rate limit reached for OpenAI API on attempt {attempt + 1}: {e}. Retrying after delay...")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Rate limit error after {max_retries} attempts for product: {product_name}. Details: {e}")
                    return []
            except APIError as e:
                self.logger.error(f"OpenAI API error on attempt {attempt + 1} for product '{product_name}': {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"API error after {max_retries} attempts for product: {product_name}. Details: {e}")
                    return []
            except Exception as e:
                self.logger.error(f"Unexpected error during product categorization for '{product_name}' on attempt {attempt + 1}: {e}")
                # Don't retry on unknown errors immediately unless sure it's transient
                return []

        self.logger.error(f"Failed to categorize product '{product_name}' after {max_retries} attempts.")
        return []

# Example Usage (requires OPENAI_API_KEY to be set in environment)
if __name__ == '__main__':
    # This will only work if you have OPENAI_API_KEY set in your environment
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY environment variable not set. Skipping live test.")
        else:
            print("Testing ProductCategorizer with OpenAI API...")
            categorizer = ProductCategorizer(api_key=api_key)

            test_products = [
                {"name": "Coca-Cola Original Taste", "brand": "Coca-Cola", "description": "Classic coke."},
                {"name": "Kraft Macaroni & Cheese Dinner Original", "brand": "Kraft"},
                {"name": "Tide PODS Laundry Detergent Pacs, Spring Meadow", "brand": "Tide"},
                {"name": "Fresh Bananas", "brand": None, "description": "A bunch of ripe bananas."},
                {"name": "Ground Beef 80/20", "brand": "Generic", "description": "1lb pack of ground beef."},
                {"name": "NonExistentProductXYZ123", "brand": "Acme"} # Test for potentially unclassifiable
            ]

            for prod in test_products:
                print(f"\nCategorizing: {prod['name']} (Brand: {prod.get('brand')})")
                categories = categorizer.categorize_product(
                    product_name=prod["name"],
                    brand=prod.get("brand"),
                    description=prod.get("description")
                )
                if categories:
                    print(f"  Categories: {categories}")
                else:
                    print(f"  Failed to categorize or no categories found.")
                time.sleep(1) # Small delay to avoid hitting rate limits if any during testing multiple items

    except ValueError as ve:
        print(f"Error initializing ProductCategorizer: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
