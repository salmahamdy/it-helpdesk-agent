import json
import requests
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


def call_groq(prompt: str) -> dict:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "temperature": GROQ_TEMPERATURE,
        "max_tokens": GROQ_MAX_TOKENS,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert IT support engineer. Always respond with valid JSON only. No markdown fences, no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    raw = response.json()
    content = raw["choices"][0]["message"]["content"].strip()

    content = content.replace("```json", "").replace("```", "").strip()

    return json.loads(content)
