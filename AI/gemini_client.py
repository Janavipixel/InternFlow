import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite"
]

def ask_gemini(prompt):
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            return response.text

        except Exception as e:
            error_message = str(e)

            if "503" in error_message:
                print(f"{model} temporarily unavailable. Trying backup...")
                continue

            raise e

    return None

if __name__ == "__main__":
    result = ask_gemini("Say hello in one word.")
    print("Final response:", result)