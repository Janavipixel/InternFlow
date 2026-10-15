import os
from dotenv import load_dotenv
from tavily import TavilyClient


def run_test():
    load_dotenv()
    api_key = os.getenv("TAVILY_API_KEY")
    print("Tavily Key loaded:", bool(api_key))
    if not api_key:
        print("TAVILY_API_KEY is not set.")
        return

    client = TavilyClient(api_key=api_key)
    response = client.search("cybersecurity internships Mumbai", max_results=2)
    print("Results count:", len(response.get("results", [])))


if __name__ == "__main__":
    run_test()