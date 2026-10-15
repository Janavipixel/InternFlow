import os
import time
import random
from dotenv import load_dotenv
from google import genai

# Load environment variables from AI/.env or root .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Supported models fallback order
DEFAULT_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
    "gemini-flash-latest",
    "gemini-2.5-flash",
]

_client = None


def get_gemini_client():
    global _client
    if _client is not None:
        return _client
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    try:
        _client = genai.Client(api_key=key)
        return _client
    except Exception as e:
        print(f"[Gemini] Error initializing client: {e}")
        return None


def ask_gemini(prompt, max_retries=2, initial_timeout=15):
    """
    Sends a generation request to the Gemini API with:
    - Safe input validation
    - Model fallback sequence
    - Bounded exponential backoff with jitter on transient failures (429 / 503)
    - Immediate graceful fallback on quota exhaustion or authentication failures
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("[Gemini] GEMINI_API_KEY is not configured.")
        return None

    client = get_gemini_client()
    if client is None:
        print("[Gemini] Client could not be created.")
        return None

    for model_name in DEFAULT_MODELS:
        for attempt in range(max_retries + 1):
            try:
                print(f"[Gemini] Requesting model '{model_name}' (attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                if response is None:
                    print(f"[Gemini] Empty response from {model_name}.")
                    break

                text = getattr(response, "text", None)
                if text and text.strip():
                    print(f"[Gemini] Successfully received response from {model_name}.")
                    return text.strip()

                print(f"[Gemini] Blank text returned from {model_name}.")
                break

            except Exception as e:
                error_msg = str(e).upper()

                # Quota exhaustion / 429: break immediately to try backup model
                if any(x in error_msg for x in ["429", "RESOURCE_EXHAUSTED", "QUOTA"]):
                    print(f"[Gemini] Quota / Rate limit reached for {model_name}. Switching to next model...")
                    break  # Fall back to next model immediately without waiting

                # Server unavailable / 503 / 500
                if any(x in error_msg for x in ["503", "UNAVAILABLE", "500"]):
                    print(f"[Gemini] Service temporarily unavailable on {model_name}.")
                    if attempt < max_retries:
                        sleep_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                        time.sleep(sleep_time)
                        continue
                    else:
                        break

                # Invalid key or permission (fatal for this key, no retry needed)
                if any(x in error_msg for x in ["401", "403", "API KEY", "PERMISSION"]):
                    print(f"[Gemini] Authentication/Permission error: {e}")
                    return None

                # Any other unexpected error
                print(f"[Gemini] Unexpected error on {model_name}: {e}")
                break

    print("[Gemini] All Gemini attempts failed. Falling back to deterministic extraction.")
    return None


if __name__ == "__main__":
    result = ask_gemini('Return JSON: {"status": "ok"}')
    print("Test result:", result)