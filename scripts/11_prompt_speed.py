"""Time Nemotron Ultra on a REAL RAG prompt, with normal vs low thinking."""
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as Timeout
import os

sys.path.insert(0, "src")
from llm import get_client
from rag import prepare

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
LIMIT = 120

prepared = prepare("What is a lexeme?")
prompt = prepared["prompt"]
print(f"Prompt length: {len(prompt)} characters\n")

SETTINGS = {
    "normal thinking": {},
    "low thinking":    {"reasoning": {"effort": "low"}},
    "thinking off":    {"reasoning": {"enabled": False}},
}


def first_word(extra):
    start = time.time()
    stream = get_client().chat.completions.create(
        model=MODEL, max_tokens=1000, temperature=0.0, stream=True,
        messages=[{"role": "user", "content": prompt}], extra_body=extra)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            return time.time() - start, chunk.choices[0].delta.content
    return time.time() - start, "(empty answer)"


pool = ThreadPoolExecutor(max_workers=3)
for name, extra in SETTINGS.items():
    job = pool.submit(first_word, extra)
    try:
        secs, word = job.result(timeout=LIMIT)
        print(f"OK    {secs:6.1f}s  {name:16} -> {word!r}")
    except Timeout:
        print(f"SLOW  >{LIMIT}s   {name}")
    except Exception as e:
        print(f"FAIL           {name:16} -> {type(e).__name__}: {str(e)[:150]}")

os._exit(0)