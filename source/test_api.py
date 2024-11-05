import os
from dotenv import load_dotenv
import openai

def test_api_connection():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: No API key found in .env file")
        return False
        
    # Set API key
    openai.api_key = api_key
    
    try:
        # Test API connection
        response = openai.Model.list()
        print("API connection successful!")
        return True
    except Exception as e:
        print(f"API connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_connection()