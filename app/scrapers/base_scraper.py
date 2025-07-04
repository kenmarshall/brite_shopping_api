from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from app.services.logger_service import logger

class BaseScraper(ABC):
    """
    Abstract base class for web scrapers.
    Each scraper should correspond to a specific store or website.
    """
    def __init__(self, store_name: str, website_url: str):
        self.store_name = store_name
        self.website_url = website_url
        self.logger = logger

    def _fetch_page(self, url: str, headers: dict = None) -> BeautifulSoup | None:
        """
        Fetches the content of a web page and returns it as a BeautifulSoup object.
        Includes basic error handling and logging.
        """
        try:
            self.logger.info(f"Fetching page: {url} for {self.store_name}")
            # Standard headers to mimic a browser
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
            }
            if headers:
                default_headers.update(headers)

            response = requests.get(url, headers=default_headers, timeout=30) # 30-second timeout
            response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)

            # Check if content type is HTML before parsing
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                self.logger.warning(f"Content type for {url} is not HTML ({content_type}). Skipping parsing.")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            self.logger.info(f"Successfully fetched and parsed page: {url}")
            return soup
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching page {url} for {self.store_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while fetching page {url} for {self.store_name}: {e}")
            return None

    @abstractmethod
    def scrape_products(self) -> list[dict]:
        """
        Abstract method to scrape product information from the website.
        Each product dictionary should ideally contain:
        - 'name' (str): Product name
        - 'brand' (str, optional): Product brand
        - 'size' (str, optional): Product size/weight (e.g., "500g", "1L")
        - 'price' (float): Product price
        - 'currency' (str, optional): Price currency (defaults to "JMD")
        - 'product_url' (str, optional): URL to the product page
        - 'image_urls' (list[str]): List of URLs for product images
        - 'description' (str, optional): Product description
        """
        pass

    @property
    def store_identifier_slug(self) -> str:
        """
        Generates a simple slug from the store name for use in synthetic place_ids.
        e.g., "Hi-Lo Food Stores" -> "hilo-food-stores"
        """
        return self.store_name.lower().replace(" ", "-").replace("'", "").replace(".", "")

    @property
    def website_domain(self) -> str:
        """
        Extracts the domain name from the website_url.
        e.g., "https://hiloshoppingja.com/shop" -> "hiloshoppingja.com"
        """
        try:
            return self.website_url.split("://")[1].split("/")[0]
        except IndexError:
            self.logger.warning(f"Could not parse domain from URL: {self.website_url}")
            # Fallback to a sanitized version of store_name if URL is malformed
            return self.store_identifier_slug + ".invalid"

    def get_synthetic_place_id(self) -> str:
        """
        Generates a synthetic place_id for stores that are scraped
        and may not have a Google Maps Place ID.
        Format: scraped:<store_slug>:<website_domain>
        """
        return f"scraped:{self.store_identifier_slug}:{self.website_domain}"

# Example usage (for illustration, will be in specific scraper files):
# class MyStoreScraper(BaseScraper):
#     def __init__(self):
#         super().__init__(store_name="My Awesome Store", website_url="https://www.myawesomestore.com/products")
#
#     def scrape_products(self) -> list[dict]:
#         self.logger.info(f"Starting scrape for {self.store_name}")
#         # soup = self._fetch_page(self.website_url)
#         # if not soup:
#         #     return []
#         # ... actual scraping logic ...
#         # Example product
#         # product = {
#         #     'name': "Awesome Product",
#         #     'brand': "AwesomeBrand",
#         #     'size': "1kg",
#         #     'price': 10.99,
#         #     'image_urls': ["https://www.myawesomestore.com/images/awesome_product.jpg"],
#         #     'product_url': "https://www.myawesomestore.com/products/awesome_product"
#         # }
#         # return [product]
#         return [] # Placeholder
#
# if __name__ == '__main__':
#     # This is just for testing the BaseScraper or individual scrapers directly
#     # Real execution will be through the ScraperAgent
#     scraper = MyStoreScraper()
#     print(f"Store Name: {scraper.store_name}")
#     print(f"Website URL: {scraper.website_url}")
#     print(f"Synthetic Place ID: {scraper.get_synthetic_place_id()}")
#     # products = scraper.scrape_products()
#     # print(f"Scraped {len(products)} products.")
#     # if products:
#     #     print("First product:", products[0])

#     # Test fetching a page (requires internet)
#     # test_soup = scraper._fetch_page("https://example.com")
#     # if test_soup:
#     #     print(f"Successfully fetched example.com: Title - {test_soup.title.string if test_soup.title else 'No title'}")
#     # else:
#     #     print("Failed to fetch example.com")

#     hilo_test_scraper = BaseScraper(store_name="Hi-Lo Test", website_url="https://hiloshoppingja.com")
#     print(f"Hi-Lo Synthetic Place ID: {hilo_test_scraper.get_synthetic_place_id()}")

#     pgj_test_scraper = BaseScraper(store_name="Shoppers Fair PGJ", website_url="https://www.pgj.world")
#     print(f"PGJ Synthetic Place ID: {pgj_test_scraper.get_synthetic_place_id()}")

#     malformed_url_scraper = BaseScraper(store_name="Malformed Test", website_url="not_a_url")
#     print(f"Malformed URL Synthetic Place ID: {malformed_url_scraper.get_synthetic_place_id()}")
#     print(f"Malformed URL domain: {malformed_url_scraper.website_domain}")

#     url_with_path = BaseScraper(store_name="Path Test", website_url="https://www.example.com/some/path/page.html")
#     print(f"URL with Path Synthetic Place ID: {url_with_path.get_synthetic_place_id()}")
#     print(f"URL with Path domain: {url_with_path.website_domain}")

#     url_http = BaseScraper(store_name="HTTP Test", website_url="http://example.com")
#     print(f"HTTP URL Synthetic Place ID: {url_http.get_synthetic_place_id()}")
#     print(f"HTTP URL domain: {url_http.website_domain}")
