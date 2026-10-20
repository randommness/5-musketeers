import os
import requests
from dotenv import load_dotenv

load_dotenv()

LLM_URL = os.getenv("LLM_API_BASE_URL", "Not found")
LLM_MODEL = "google/gemini-3.1-flash-lite"

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert assistant for a pet care business that sells products, "
    "services, and treatments. You help analyse customer data and provide "
    "concise, helpful insights. Always respond in plain text, no markdown."
)

def chat(user_prompt: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
    api_key = os.getenv("LLM_API_KEY")

    response = requests.post(
        LLM_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(chat("Hi"))