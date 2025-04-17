import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API key

# Optional: Add a function to test the OpenAI connection
def test_openai_connection():
    try:
        # TODO: The resource 'Engine' has been deprecated
        # response = openai.Engine.list()
        print("OpenAI connection successful!")
    except Exception as e:
        print(f"Error connecting to OpenAI: {e}")