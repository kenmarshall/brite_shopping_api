import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API key
openai.api_key = os.getenv("OPEN_AI_KEY")

# Optional: Add a function to test the OpenAI connection
def test_openai_connection():
    try:
        response = openai.Engine.list()
        print("OpenAI connection successful!")
    except Exception as e:
        print(f"Error connecting to OpenAI: {e}")