"""Test each model on its own: does it answer, and how fast? (Key is never printed.)"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as Timeout

import requests
from dotenv import load_dotenv

sys.path.insert(0, "src")
from llm import MODELS, get_client

load_dotenv()
LIMIT = 30          # seconds we are willing to wait per model

# 1. Is the key valid, and how much free usage is left?
r = requests.get("https://openrouter.ai/api/v1/key",
                 headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
                 timeout=15)
print("Key check:", r.status_code)
if r.ok:
    d = r.json().get("data", {})
    print("  free tier:", d.get("is_free_tier"), "| usage:", d.get("usage"),
          "| limit remaining:", d.get("limit_remaining"))
else:
    print("  ", r.text[:200])


def first_word(model):
    """Stream a tiny question; return seconds until the first real word."""
    start = time.time()
    stream = get_client().chat.completions.create(
        model=model, max_tokens=50, stream=True,
        messages=[{"role": "user", "content": "Say hello in 3 words."}])
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            return time.time() - start, chunk.choices[0].delta.content
    return time.time() - start, "(empty answer)"


# 2. Time each model separately
pool = ThreadPoolExecutor(max_workers=len(MODELS))
for model in MODELS:
    job = pool.submit(first_word, model)
    try:
        secs, word = job.result(timeout=LIMIT)
        print(f"OK    {secs:5.1f}s  {model}  -> {word!r}")
    except Timeout:
        print(f"SLOW  >{LIMIT}s   {model}")
    except Exception as e:
        print(f"FAIL          {model}  -> {type(e).__name__}: {str(e)[:120]}")

os._exit(0)          # don't wait for slow models still running in the background