from app.services.logger_service import logger
from app.models.product_model import ProductModel
from app.models.store_model import StoreModel
from app.models.product_price_model import ProductPriceModel
from app.scrapers.s3_uploader import S3Uploader
from app.scrapers.product_categorizer import ProductCategorizer
from app.scrapers.base_scraper import BaseScraper # For type hinting
import os # For environment variables for Categorizer and S3Uploader defaults

class ScraperAgent:
    """
    Orchestrates the web scraping process:
    - Takes a list of scraper instances.
    - For each scraper:
        - Gets or creates a store record.
        - Calls the scraper to get product data.
        - For each product:
            - Categorizes the product using ProductCategorizer.
            - Uploads images to S3 using S3Uploader.
            - Saves product data to MongoDB using ProductModel.
            - Saves price data to MongoDB using ProductPriceModel.
    """
    def __init__(self):
        self.logger = logger
        # Initialize services. Credentials/keys are typically handled within these classes via environment variables.
        # Consider passing configuration if not using environment variables directly in those classes.
        self.s3_uploader = S3Uploader() # Relies on AWS_ env vars
        self.categorizer = ProductCategorizer() # Relies on OPENAI_API_KEY env var

        # Check if services were initialized correctly (e.g. S3 client in S3Uploader)
        if not self.s3_uploader.s3_client:
            self.logger.warning("S3Uploader might not be correctly configured (missing credentials or bucket info). Image uploads may fail.")
        # ProductCategorizer raises ValueError if API key is missing, so it would have failed on init if so.

    def run_scrapers(self, scraper_instances: list[BaseScraper]):
        """
        Runs the provided list of scraper instances.

        :param scraper_instances: A list of initialized scraper objects (e.g., [HiloScraper(), ShoppersFairScraper()]).
        """
        if not scraper_instances:
            self.logger.info("No scraper instances provided to ScraperAgent. Nothing to do.")
            return

        self.logger.info(f"ScraperAgent started. Processing {len(scraper_instances)} scraper(s).")

        for scraper in scraper_instances:
            self.logger.info(f"Processing store: {scraper.store_name} ({scraper.website_url})")

            # 1. Get or create Store ID
            synthetic_place_id = scraper.get_synthetic_place_id()
            store_data = {
                "store": scraper.store_name, # This is the 'name' field for StoreModel
                "place_id": synthetic_place_id,
                "website": scraper.website_url,
                # Other fields like address, lat, lng could be added if known,
                # but are not strictly required by StoreModel.get_or_create if not present.
                # Ensure 'store' (name) is not None. BaseScraper should ensure store_name is set.
            }
            try:
                store_id = StoreModel.get_or_create(store_data)
                self.logger.info(f"Store '{scraper.store_name}' (ID: {store_id}) ensured in database.")
            except ValueError as e:
                self.logger.error(f"Failed to get or create store '{scraper.store_name}': {e}. Skipping this scraper.")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error getting/creating store '{scraper.store_name}': {e}. Skipping this scraper.")
                continue

            # 2. Scrape products from the current scraper
            try:
                scraped_product_items = scraper.scrape_products()
                self.logger.info(f"Scraper for {scraper.store_name} returned {len(scraped_product_items)} item(s).")
            except Exception as e:
                self.logger.error(f"Error during scraping for {scraper.store_name}: {e}. Skipping this scraper.")
                continue

            if not scraped_product_items:
                self.logger.info(f"No products found or scraped by {scraper.store_name}. Moving to next scraper.")
                continue

            for item in scraped_product_items:
                try:
                    product_name = item.get("name")
                    if not product_name:
                        self.logger.warning(f"Skipping item due to missing product name from {scraper.store_name}. Item data: {item}")
                        continue

                    self.logger.info(f"Processing item: '{product_name}' from {scraper.store_name}")

                    # 3. Categorize product
                    categories = self.categorizer.categorize_product(
                        product_name=product_name,
                        brand=item.get("brand"),
                        description=item.get("description")
                    )

                    # 4. Upload images to S3
                    s3_image_urls = []
                    if self.s3_uploader.s3_client: # Only attempt if S3 client is available
                        for img_url in item.get("image_urls", []):
                            s3_url = self.s3_uploader.upload_image_from_url(img_url, product_name=product_name)
                            if s3_url:
                                s3_image_urls.append(s3_url)
                    elif item.get("image_urls"):
                        self.logger.warning(f"S3 client not available. Skipping image uploads for '{product_name}'.")


                    # 5. Prepare product data for ProductModel
                    product_data_for_db = {
                        "name": product_name,
                        "brand": item.get("brand"),
                        "size": item.get("size"), # Weight/volume
                        "description": item.get("description"),
                        "image_urls": s3_image_urls, # List of S3 URLs
                        "categories": categories, # List of strings from categorizer
                        "source_website": scraper.website_url, # Website it was scraped from
                        "product_source_url": item.get("product_url") # Specific product page URL
                    }
                    # Filter out None values to avoid inserting them, unless model handles it
                    product_data_for_db = {k: v for k, v in product_data_for_db.items() if v is not None}


                    # 6. Get or create Product ID (ProductModel handles embedding for new products)
                    try:
                        product_id = ProductModel.get_or_create_product(product_data_for_db)
                        self.logger.info(f"Product '{product_name}' (ID: {product_id}) ensured in database.")
                    except ValueError as e:
                        self.logger.error(f"ValueError saving product '{product_name}': {e}. Skipping this item.")
                        continue
                    except Exception as e: # Catch other potential db errors
                        self.logger.error(f"Error saving product '{product_name}' to DB: {e}. Skipping this item.")
                        continue

                    # 7. Upsert Product Price
                    price = item.get("price")
                    if price is not None:
                        try:
                            # Ensure price is float
                            price = float(price)
                            currency = item.get("currency", "JMD") # Default currency
                            ProductPriceModel.upsert_price(
                                product_id=str(product_id),
                                store_id=str(store_id),
                                price=price,
                                currency=currency
                            )
                            self.logger.info(f"Price {price} {currency} for product '{product_name}' at store '{scraper.store_name}' upserted.")
                        except ValueError as e: # Handles float conversion error
                            self.logger.error(f"Invalid price format for '{product_name}': {price}. Skipping price update. Error: {e}")
                        except Exception as e:
                             self.logger.error(f"Error upserting price for product '{product_name}': {e}. Skipping price update.")
                    else:
                        self.logger.info(f"No price found for product '{product_name}' in scraped data. Skipping price update.")

                except Exception as e:
                    self.logger.error(f"Unhandled error processing item '{item.get('name', 'Unknown item')}' from {scraper.store_name}: {e}")
                    # Continue to the next item

        self.logger.info("ScraperAgent finished processing all scrapers.")

# Example usage (would typically be in run_scraper.py)
if __name__ == '__main__':
    # This is for conceptual testing.
    # It requires:
    # - MongoDB running and accessible via app.db
    # - Environment variables for OpenAI and AWS S3 set up.
    # - Implemented HiloScraper and ShoppersFairScraper (currently they return empty lists).

    # --- Mocking for demonstration ---
    class MockScraper(BaseScraper):
        def __init__(self, store_name, website_url, products_to_return):
            super().__init__(store_name, website_url)
            self.products_to_return = products_to_return

        def scrape_products(self) -> list[dict]:
            self.logger.info(f"MockScraper: Returning {len(self.products_to_return)} mock products for {self.store_name}.")
            return self.products_to_return

    # Ensure environment variables are loaded if using a .env file for testing locally
    # from dotenv import load_dotenv
    # load_dotenv()

    # Check if essential env vars are present before trying to run
    required_env_vars = ["OPENAI_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_BUCKET_NAME", "AWS_REGION", "MONGO_URI"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Cannot run ScraperAgent example: Missing environment variables: {', '.join(missing_vars)}")
        print("Please ensure MongoDB is running and all necessary API keys/credentials are set.")
    else:
        print("Starting ScraperAgent example with MockScrapers...")

        # Sample product data that mock scrapers would return
        mock_hilo_products = [
            {
                'name': "Grace Ketchup Test", 'brand': "Grace", 'size': "350ml", 'price': 350.00,
                'image_urls': ["https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"], # Test image
                'product_url': "https://hiloshoppingja.com/product/grace-ketchup-test",
                'description': "Test Grace Ketchup from mock."
            },
            {
                'name': "Test Bread Loaf", 'brand': "National", 'size': "Standard", 'price': 250.50,
                'image_urls': [], # No image for this one
                'product_url': "https://hiloshoppingja.com/product/test-bread",
                'description': "A loaf of test bread."
            }
        ]
        mock_sf_products = [
            {
                'name': "CB Whole Chicken Test", 'brand': "CB", 'size': "1.5kg", 'price': 1250.00,
                'image_urls': ["https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"], # Another test image
                'product_url': "https://www.pgj.world/product/cb-chicken-test",
                'description': "Test CB whole chicken from mock."
            }
        ]

        # Initialize mock scrapers
        # These URLs are just for the example; BaseScraper uses them for synthetic_place_id
        hilo_mock_scraper = MockScraper(store_name="Hi-Lo Mock Store", website_url="https://hiloshoppingja.com/mock", products_to_return=mock_hilo_products)
        sf_mock_scraper = MockScraper(store_name="Shoppers Fair Mock", website_url="https://www.pgj.world/mock", products_to_return=mock_sf_products)

        # Initialize and run the agent
        agent = ScraperAgent()
        agent.run_scrapers([hilo_mock_scraper, sf_mock_scraper])

        print("ScraperAgent example run completed. Check logs and database for results.")
        print("Note: Actual HiloScraper and ShoppersFairScraper need full implementation to get real data.")
