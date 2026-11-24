import os
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, InternalServerError, APITimeoutError

load_dotenv()

MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "inclusionai/ling-3.2-flash:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "openrouter/free",                 # last resort: any available free model
]
RETRYABLE_ERRORS = (RateLimitError, InternalServerError, APITimeoutError)

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found. Check your .env file.")
        _client = OpenAI(base_url="https://openrouter.ai/api/v1",
                         api_key=api_key, timeout=60)
    return _client


def generate(prompt, max_tokens=1000, temperature=0.0):
    """Send one prompt, return (answer_text, model_used). Retries and falls back."""
    for model in MODELS:
        for attempt in range(2):
            try:
                response = get_client().chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.choices[0].message.content
                if text:                         # skip empty replies
                                        return text.strip(), response.model or model
            except RETRYABLE_ERRORS as e:
                print(f"  {model} failed (try {attempt + 1}): "
                      f"{type(e).__name__} - {getattr(e, 'body', e)}")
                time.sleep(10)
    raise RuntimeError("All models failed. Try again in a few minutes.")