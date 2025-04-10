import logging
import requests
import os

class HTTPLogHandler(logging.Handler):
    """
    Custom logging handler that sends log messages via HTTP POST requests.
    """
    def __init__(self):
        super().__init__()
        self.endpoint_url = "https://s1269448.eu-nbg-2.betterstackdata.com/"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('TELEMETRY_SOURCE_TOKEN')}"
        }

    def emit(self, record):
        try:
            log_entry = self.format(record)
            response = requests.post(self.endpoint_url, json={"log": log_entry})
            response.raise_for_status()  # Raise an error for HTTP errors
        except Exception as e:
            # Handle exceptions silently to avoid breaking the application
            print(f"Failed to send log: {e}")

# Logger setup
def setup_logger(endpoint_url):
    logger = logging.getLogger("HTTPLogger")
    logger.setLevel(logging.DEBUG)  # Set the desired log level

    # Create and add the custom HTTP handler
    http_handler = HTTPLogHandler(endpoint_url)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    http_handler.setFormatter(formatter)
    logger.addHandler(http_handler)

    return logger