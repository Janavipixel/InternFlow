import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = None

if api_key:
    client = genai.Client(
        api_key=api_key
    )

MODEL = "gemini-3.6-flash"


def ask_gemini(prompt):

    if not api_key:
        print("GEMINI_API_KEY is missing.")
        return None

    if client is None:
        print("Gemini client could not be created.")
        return None

    try:
        print("Sending request to Gemini...")

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        if response is None:
            print("Gemini returned no response.")
            return None

        text = getattr(response, "text", None)

        if not text:
            print("Gemini returned empty response.")
            return None

        print("Gemini response received.")

        return text

    except Exception as e:

        error_message = str(e).upper()

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
            or "QUOTA" in error_message
            or "RATE LIMIT" in error_message
        ):
            print("Gemini quota/rate limit reached.")
            print("Gemini request stopped.")
            return None

        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
            or "500" in error_message
        ):
            print("Gemini service temporarily unavailable.")
            return None

        if (
            "401" in error_message
            or "403" in error_message
            or "API KEY" in error_message
            or "PERMISSION" in error_message
        ):
            print("Gemini API key or permission problem.")
            print(e)
            return None

        print("Gemini error:")
        print(e)

        return None


if __name__ == "__main__":

    result = ask_gemini(
        """
        Return ONLY valid JSON.

        {
            "message": "hello"
        }
        """
    )

    print("Final response:")
    print(result)