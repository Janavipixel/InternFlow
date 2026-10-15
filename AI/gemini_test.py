import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not configured.")
        return
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello in one word."
    )
    print(getattr(response, "text", "No text"))


if __name__ == "__main__":
    test_gemini()