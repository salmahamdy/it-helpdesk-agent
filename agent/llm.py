import json
import time
import requests
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

MAX_RETRIES = 3
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

SYSTEM_MSG = (
    "You are an expert IT support engineer. Always respond with valid JSON only. "
    "No markdown fences, no explanation."
)


def call_groq(prompt: str) -> dict:
    """Send a prompt to Groq and return a parsed JSON dict.

    Raises ValueError if the API key is missing, RuntimeError if the request
    keeps failing after retries, or json.JSONDecodeError if the model returns
    unparseable output even after one repair attempt.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set.")

    content = _request_with_retries(prompt)
    return _parse_json(content)


def _request_with_retries(prompt: str) -> str:
    """POST to Groq with exponential backoff on transient errors. Returns the
    raw message content string."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "temperature": GROQ_TEMPERATURE,
        "max_tokens": GROQ_MAX_TOKENS,
        # Step 2a: force valid JSON at the API level, not just via the prompt.
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": prompt},
        ],
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)

            # Step 3: retry transient server / rate-limit errors with backoff.
            if resp.status_code in RETRYABLE_STATUS:
                last_error = f"HTTP {resp.status_code}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(_backoff_seconds(attempt, resp))
                    continue
                resp.raise_for_status()

            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

        except requests.RequestException as e:
            # Network errors / timeouts are also transient -> back off and retry.
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(_backoff_seconds(attempt))
                continue
            raise RuntimeError(
                f"Groq request failed after {MAX_RETRIES} attempts: {last_error}"
            ) from e

    raise RuntimeError(f"Groq request failed after {MAX_RETRIES} attempts: {last_error}")


def _backoff_seconds(attempt: int, resp=None) -> float:
    """Exponential backoff (1s, 2s, 4s...). Honors Retry-After on 429s."""
    if resp is not None and resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return 2.0 ** attempt


def _strip_fences(content: str) -> str:
    return content.replace("```json", "").replace("```", "").strip()


def _parse_json(content: str) -> dict:
    """Parse JSON, with one self-repair retry if the first parse fails (Step 2b)."""
    try:
        return json.loads(_strip_fences(content))
    except json.JSONDecodeError:
        repair_prompt = (
            "The text below was meant to be a single valid JSON object but did not "
            "parse. Return ONLY the corrected JSON object, with no commentary:\n\n"
            f"{content}"
        )
        repaired = _request_with_retries(repair_prompt)
        # If this still fails, the JSONDecodeError propagates to the caller,
        # which app.py surfaces as a clean error message.
        return json.loads(_strip_fences(repaired))
