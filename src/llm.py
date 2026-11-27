import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FirstWordTimeout

from dotenv import load_dotenv
from openai import (OpenAI, APIError, AuthenticationError,
                    RateLimitError, InternalServerError, APITimeoutError)

load_dotenv()

MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",              # best answers (used in Day 11 eval)
    "google/gemma-4-31b-it:free",                          # fast, no "thinking" step
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "openrouter/free",                                     # last resort: any available free model
]
RETRYABLE_ERRORS = (RateLimitError, InternalServerError, APITimeoutError)
FIRST_WORD_LIMIT = 25      # seconds to wait for a model's first word before trying the next
CUT_OFF = "\n\n_(The answer was cut off by the model service. Please ask again.)_"

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
    """Send one prompt, return (answer_text, model_used). Retries and falls back.
    (Used by the eval scripts, which don't need streaming.)"""
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


def _text_pieces(stream):
    """Generator: yield each small piece of text as it arrives."""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def _rest_of_answer(first, pieces):
    """Generator: the first piece we already have, then the rest.
    If the stream breaks midway, end with a short note instead of crashing."""
    yield first
    try:
        yield from pieces
    except APIError as e:
        print(f"  stream cut off midway: {type(e).__name__} - {e}")
        yield CUT_OFF


def _start_and_get_first_word(model, prompt, max_tokens, temperature):
    """Open a stream and wait for its first real piece. Returns (first, pieces);
    first is None if the model finished without saying anything."""
    stream = get_client().chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    pieces = _text_pieces(stream)
    return next(pieces, None), pieces


def generate_stream(prompt, max_tokens=1000, temperature=0.0):
    """Start a streamed answer. Returns (model_used, generator of text pieces).
    Each model gets FIRST_WORD_LIMIT seconds to say its first word; if it is
    too slow, errors, or says nothing, we move straight to the next model."""
    for model in MODELS:
        helper = ThreadPoolExecutor(max_workers=1)          # runs the wait in the background
        job = helper.submit(_start_and_get_first_word, model, prompt, max_tokens, temperature)
        try:
            first, pieces = job.result(timeout=FIRST_WORD_LIMIT)
        except FirstWordTimeout:
            print(f"  {model}: no first word in {FIRST_WORD_LIMIT}s, trying next model")
            continue
        except AuthenticationError:                         # wrong key: every model would fail
            raise
        except APIError as e:                               # 429, 503, 404, error inside stream...
            print(f"  {model} failed: {type(e).__name__} - {getattr(e, 'body', e)}")
            continue
        finally:
            helper.shutdown(wait=False)                     # never wait for a slow model

        if first is None:
            print(f"  {model}: empty answer, trying next model")
            continue
        return model, _rest_of_answer(first, pieces)
    raise RuntimeError("All models failed. Try again in a few minutes.")