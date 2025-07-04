from app.scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup # Explicitly import for clarity, though _fetch_page returns soup
from urllib.parse import urljoin # For making relative URLs absolute

# IMPORTANT: The HTML structure and selectors used below are examples
# and WILL LIKELY NEED ADJUSTMENT based on the actual live website structure
# of hiloshoppingja.com. This is a mocked implementation for demonstration.

class HiloScraper(BaseScraper):
    """
    Scraper for Hi-Lo Food Stores (hiloshoppingja.com).
    """
    def __init__(self):
        super().__init__(store_name="Hi-Lo Food Stores", website_url="https://hiloshoppingja.com")
        # This should be the URL to their main shop page or a page listing categories/products.
        self.start_url = "https://hiloshoppingja.com/shop/"
        # Example: If Hi-Lo has category pages, you might iterate through them:
        # self.category_urls = [
        #     "https://hiloshoppingja.com/shop/category/dairy",
        #     "https://hiloshoppingja.com/shop/category/beverages",
        # ]

    def _parse_product_card(self, product_card_soup: BeautifulSoup, card_url: str) -> dict | None:
        """
        Parses a single product 'card' element from a listing page.
        This is highly dependent on the website's HTML structure.
        """
        try:
            # --- Example Selectors (these are guesses) ---
            name_tag = product_card_soup.select_one(".product-name a, .woocommerce-loop-product__title, .product-title a")
            price_tag = product_card_soup.select_one(".price .woocommerce-Price-amount, .product-price, .price-wrapper .amount")
            image_tag = product_card_soup.select_one(".product-image img, .attachment-woocommerce_thumbnail, .product-thumbnail img")

            name_link_tag = None
            if name_tag and name_tag.name == 'a': # If the name tag itself is a link
                 name_link_tag = name_tag
            elif name_tag: # If name_tag is H2, H3 etc, look for an 'a' tag within or parent 'a'
                name_link_tag = name_tag.find('a') or product_card_soup.find('a', class_=["product-image-link", "product-item-link"])


            name = name_tag.text.strip() if name_tag else None
            if not name:
                # Try another common pattern for names if the first failed
                name_tag_alt = product_card_soup.select_one('a[title]')
                if name_tag_alt:
                    name = name_tag_alt.get('title','').strip()

            if not name:
                self.logger.warning(f"Could not find product name in card on {card_url}. Card HTML: {str(product_card_soup)[:200]}")
                return None

            price_str = price_tag.get_text(separator=' ', strip=True) if price_tag else None
            price = None
            if price_str:
                # Enhanced price cleaning: remove currency symbols/codes, commas, then extract numbers
                # Handles "JMD 1,200.50", "$350.00", "1500"
                import re
                # Remove common currency symbols and codes, then non-numeric/non-decimal point characters except comma
                price_str_cleaned = re.sub(r'(JMD|USD|\$|€|£)', '', price_str, flags=re.IGNORECASE)
                price_str_cleaned = re.sub(r'[^\d\.]', '', price_str_cleaned) # Keep only digits and decimal point
                try:
                    if price_str_cleaned:
                        price = float(price_str_cleaned)
                except ValueError:
                    self.logger.warning(f"Could not parse price '{price_str}' to float for product '{name}'. Cleaned: '{price_str_cleaned}'")


            image_url = None
            if image_tag:
                # Prioritize 'data-src', 'data-lazy-src', then 'src'
                image_url = image_tag.get('data-src') or image_tag.get('data-lazy-src') or image_tag.get('src')
                if image_url and not image_url.startswith(('http:', 'https:', '//')):
                    image_url = urljoin(self.website_url, image_url) # Ensure absolute URL
                elif image_url and image_url.startswith('//'): # Handle protocol-relative URLs
                    image_url = "https:" + image_url

            product_page_url = None
            if name_link_tag and name_link_tag.get('href'):
                product_page_url = name_link_tag.get('href')
                if not product_page_url.startswith(('http:', 'https:', '//')):
                     product_page_url = urljoin(self.website_url, product_page_url)
                elif product_page_url.startswith('//'):
                     product_page_url = "https:" + product_page_url
            else: # Fallback if no specific link found associated with name or image
                product_page_url = card_url

            product_data = {
                'name': name,
                'brand': None,
                'size': None,
                'price': price,
                'currency': "JMD",
                'product_url': product_page_url,
                'image_urls': [image_url] if image_url else [],
                'description': None,
                'scraped_from_url': card_url
            }
            self.logger.debug(f"Parsed product from card: {product_data.get('name')}, Price: {product_data.get('price')}")
            return product_data

        except Exception as e:
            self.logger.error(f"Error parsing product card on {card_url}: {e}", exc_info=True)
            return None

    def scrape_products(self) -> list[dict]:
        self.logger.info(f"Starting scrape for {self.store_name} from {self.start_url}")
        all_products = []

        mock_html_content = """
        <html><head><title>Shop - Hi-Lo</title></head>
        <body>
            <ul class="products-grid">
                <li class="product-item">
                    <a href="/product/grace-ketchup" class="product-image-link">
                        <img src="/images/grace_ketchup_thumb.jpg" class="product-thumbnail" alt="Grace Ketchup">
                    </a>
                    <h2 class="woocommerce-loop-product__title"><a href="/product/grace-ketchup">Grace Ketchup Original</a></h2>
                    <span class="price-wrapper"><span class="price"><span class="woocommerce-Price-amount amount"><bdi>350<span class="woocommerce-Price-currencySymbol">.00</span></bdi></span></span></span>
                    <div class="product-brand">Grace</div>
                    <div class="product-size">350ml</div>
                </li>
                <li class="product-item">
                    <a href="/product/national-whole-wheat" class="product-item-link">
                         <img data-lazy-src="//cdn.example.com/images/national_bread_thumb.webp" class="product-thumbnail lazyload" alt="National Bread">
                    </a>
                    <h3 class="product-title"><a href="/product/national-whole-wheat">National Whole Wheat Bread</a></h3>
                    <div class="price"><span class="woocommerce-Price-amount amount"><bdi>JMD 280<span class="woocommerce-Price-currencySymbol">.00</span></bdi></span></div>
                </li>
                <li class="product type-product">
                    <h2 class="product-name"><a title="Special Item (Price TBD)" href="/product/special-item">Special Item (Price TBD)</a></h2>
                    <img src="https://othersite.com/images/special_item.png" class="product-image">
                </li>
                 <li class="product"> <!-- A slightly different structure -->
                    <a class="product-link" href="/product/premium-item">
                        <img src="/images/premium_item.jpg" class="product-main-image">
                        <span class="product-name-span">Premium Item</span>
                    </a>
                     <div class="price-tag"><span class="value">1,200.50</span></div>
                </li>
            </ul>
        </body></html>
        """
        # soup = self._fetch_page(self.start_url) # Real usage
        soup = BeautifulSoup(mock_html_content, 'html.parser') # Mock usage

        if not soup:
            self.logger.error(f"Could not fetch or parse the start page for {self.store_name}: {self.start_url}")
            return []

        # More general selectors for product items/cards
        product_cards = soup.select("li.product-item, .product.type-product, li.product, div.product-card")

        if not product_cards:
            self.logger.warning(f"No product cards found on {self.start_url} using selectors. Check website structure.")
            return []

        self.logger.info(f"Found {len(product_cards)} potential product cards on {self.start_url}.")

        for card_soup in product_cards:
            parsed_data = self._parse_product_card(card_soup, self.start_url)
            if parsed_data:
                # Mock extracting brand/size if available directly in card (as per mock HTML)
                if not parsed_data.get('brand'):
                    brand_tag_mock = card_soup.select_one(".product-brand, .product-manufacturer")
                    if brand_tag_mock: parsed_data['brand'] = brand_tag_mock.text.strip()

                if not parsed_data.get('size'):
                    size_tag_mock = card_soup.select_one(".product-size, .product-weight")
                    if size_tag_mock: parsed_data['size'] = size_tag_mock.text.strip()

                # If still no brand, try to infer from name (simple split)
                if not parsed_data.get('brand') and parsed_data.get('name'):
                    name_parts = parsed_data['name'].split(" ")
                    if len(name_parts) > 1: # Potentially first word is brand
                        # This is a very naive way, real brand extraction is complex
                        # For example, "Grace Ketchup" -> "Grace"
                        # Check against a known list of brands or patterns if possible
                        pass # parsed_data['brand'] = name_parts[0] # Example, needs refinement

                all_products.append(parsed_data)

        self.logger.info(f"Successfully scraped {len(all_products)} products from {self.store_name} (mocked data).")
        return all_products

if __name__ == '__main__':
    print(f"Testing {HiloScraper().store_name} scraper (with mocked HTML)...")
    scraper = HiloScraper()

    products = scraper.scrape_products()
    if products:
        print(f"\nScraped {len(products)} products (mocked data):")
        for i, product in enumerate(products):
            print(f"--- Product {i+1} ---")
            print(f"  Name: {product.get('name')}")
            print(f"  Brand: {product.get('brand')}")
            print(f"  Size: {product.get('size')}")
            print(f"  Price: {product.get('price')} {product.get('currency')}")
            print(f"  Image URLs: {product.get('image_urls')}")
            print(f"  Product URL: {product.get('product_url')}")
    else:
        print("No products scraped (mocked data).")

    print(f"\nNote: This uses MOCKED HTML. Actual selectors for hiloshoppingja.com will differ significantly.")
