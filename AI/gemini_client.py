
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


def ask_gemini(prompt):

    if not api_key:
        raise Exception("GEMINI_API_KEY is missing.")

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        error_message = str(e).upper()

        # Gemini quota / rate limit
        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
            or "QUOTA" in error_message
            or "RATE LIMIT" in error_message
        ):
            print("Gemini quota/rate limit reached.")
            print("Stopping Gemini request.")
            return None

        # Temporary Gemini/server problem
        if "503" in error_message or "UNAVAILABLE" in error_message:
            print("Gemini service temporarily unavailable.")
            return None

        # Other Gemini error
        print("Gemini error:", e)
        return None


if __name__ == "__main__":
    result = ask_gemini("Say hello in one word.")
    print("Final response:", result)
