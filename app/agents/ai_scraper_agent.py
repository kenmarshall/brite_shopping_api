import json
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool
from app.services.logger_service import logger
from app.models.product_model import ProductModel
from app.scrapers.s3_uploader import s3_uploader

# --- Tool Definitions ---

@tool
def search_web(query: str) -> str:
    """Search the web for the given query and return HTML of the results page."""
    logger.info(f"Searching web for: {query}")
    resp = requests.get(
        "https://duckduckgo.com/html/", params={"q": query}, timeout=10
    )
    resp.raise_for_status()
    return resp.text

@tool
def fetch_page(url: str) -> str:
    """Fetch raw HTML for a page."""
    logger.info(f"Fetching page: {url}")
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text

@tool
def parse_html(html: str) -> List[Dict[str, str]]:
    """Extract product info from HTML using simple heuristics."""
    soup = BeautifulSoup(html, "html.parser")
    products = []
    for item in soup.select("div, li"):
        text = item.get_text(" ", strip=True)
        if re.search(r"\b(?:price|jmd|jamaican)\b", text, re.I):
            name = text[:100]
            img = item.find("img")
            img_url = img["src"] if img else None
            products.append({"raw_text": name, "image": img_url})
    return products

@tool
def categorize_product(name: str) -> List[str]:
    """Use an LLM to assign up to 5 categories to a product."""
    llm = ChatOpenAI(temperature=0)
    prompt = (
        "Categorize the following product into up to 5 short categories. "
        "Return as a JSON list of strings. Product: " + name
    )
    resp = llm.predict(prompt)
    try:
        cats = json.loads(resp)
        if isinstance(cats, list):
            return cats
    except Exception:
        pass
    return []

@tool
def upload_image(url: str) -> str:
    """Upload an image to S3 and return the public URL."""
    return s3_uploader.upload_image_from_url(url)

@tool
def save_product(name: str, source_url: str, image_url: str, categories: List[str]):
    """Save product data to MongoDB."""
    data = {
        "name": name,
        "source_url": source_url,
        "image_url": image_url,
        "categories": categories,
    }
    ProductModel.get_or_create_product(data)
    return "saved"

TOOLS = [search_web, fetch_page, parse_html, categorize_product, upload_image, save_product]


def create_agent() -> "AgentExecutor":
    llm = ChatOpenAI(temperature=0)
    agent = initialize_agent(
        TOOLS,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
    )
    return agent


def run(task: str):
    agent = create_agent()
    agent.run(task)

