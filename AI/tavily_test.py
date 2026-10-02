import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

print("Key loaded:", api_key is not None)
print("Key prefix:", api_key[:5] if api_key else None)

client = TavilyClient(api_key=api_key)

response = client.search("cybersecurity internships Mumbai")

print(response)