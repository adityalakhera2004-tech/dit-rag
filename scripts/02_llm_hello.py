import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, InternalServerError, APITimeoutError

load_dotenv()  # reads OPENROUTER_API_KEY from .env

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Check your .env file.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    timeout=60,  # give up on a single request after 60 seconds
)

# Try models in order: if one fails, fall back to the next
MODELS = [
    "google/gemma-4-31b-it:free",
    "inclusionai/ling-3.2-flash:free",
]

# Temporary errors worth retrying: busy (429), server error/timeout (5xx), network timeout
RETRYABLE_ERRORS = (RateLimitError, InternalServerError, APITimeoutError)


def ask(question):
    for model in MODELS:
        for attempt in range(2):  # 2 tries per model
            try:
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=200,
                    messages=[{"role": "user", "content": question}],
                )
                print(f"[answered by {model}]")
                return response.choices[0].message.content
            except RETRYABLE_ERRORS as e:
                print(f"{model} failed (try {attempt + 1}): {type(e).__name__} - {e}")
                time.sleep(10)
    return "All models failed right now. Try again in a few minutes."


print(ask("In one line: what is RAG?"))