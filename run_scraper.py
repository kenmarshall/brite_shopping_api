import os
from dotenv import load_dotenv

from app.scrapers.scraper_agent import ScraperAgent
from app.scrapers.hilo_scraper import HiloScraper
from app.scrapers.shoppers_fair_scraper import ShoppersFairScraper
from app.services.logger_service import logger

# It's good practice to explicitly load environment variables at the start of your script,
# especially for an entry point like this.
# This ensures that all necessary configurations (API keys, DB URIs, etc.) are available.
load_dotenv() # Loads variables from .env file into environment variables

def main():
    """
    Main function to initialize and run the web scraping agent.
    """
    logger.info("Starting the scraping process via run_scraper.py...")

    # --- Configuration & Setup ---
    # Check for essential environment variables needed by the agent/scrapers/services
    # This is a good place for a pre-flight check.
    required_env_vars = [
        "MONGO_URI",            # For database connection (used by app.db)
        "OPENAI_API_KEY",       # For ProductCategorizer
        "AWS_ACCESS_KEY_ID",    # For S3Uploader
        "AWS_SECRET_ACCESS_KEY",# For S3Uploader
        "AWS_S3_BUCKET_NAME",   # For S3Uploader
        "AWS_REGION"            # For S3Uploader
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Essential environment variable(s) are missing: {', '.join(missing_vars)}")
        logger.error("Scraping process cannot start without these configurations. Please set them up.")
        return

    logger.info("All essential environment variables seem to be present.")

    # --- Initialize Scrapers ---
    # Instantiate the specific scrapers you want to run.
    # These will be passed to the ScraperAgent.
    hilo_scraper = HiloScraper()
    shoppers_fair_scraper = ShoppersFairScraper()
    # Add more scraper instances here as they are developed
    # e.g., another_store_scraper = AnotherStoreScraper()

    scrapers_to_run = [
        hilo_scraper,
        shoppers_fair_scraper,
        # another_store_scraper,
    ]

    if not scrapers_to_run:
        logger.info("No scrapers configured to run. Exiting.")
        return

    logger.info(f"Initialized {len(scrapers_to_run)} scraper(s): {[s.store_name for s in scrapers_to_run]}")

    # --- Initialize and Run the ScraperAgent ---
    try:
        agent = ScraperAgent()
        logger.info("ScraperAgent initialized. Starting run_scrapers...")
        agent.run_scrapers(scrapers_to_run)
        logger.info("ScraperAgent has completed its run.")
    except ValueError as ve: # Catch specific init errors like missing API key in ProductCategorizer
        logger.error(f"Failed to initialize ScraperAgent or its components: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during the scraping process: {e}", exc_info=True)
        # exc_info=True will include traceback in the log for better debugging

    logger.info("Scraping process finished.")

if __name__ == "__main__":
    # This allows the script to be run directly using `python run_scraper.py`
    main()
