# Design notes

## Day 1: Embedding experiment (bge-small-en-v1.5, 4 toy chunks)
- With "CSN 401" in the query: correct chunk won by only 0.002 (wrong chunk won with prefix).
- Without course code: correct chunk won by 0.087 (~40x bigger gap).
- Decision: extract course code → metadata filter; embed only the rest of the question.
- bge query prefix: no improvement on this toy test. Re-test on the 30-question eval (Day 11).

## Day 1: LLM provider (OpenRouter)
- Free models share a common rate-limit pool → frequent 429 (busy), 503/504 (server/timeout).
- Added: retry with wait, fallback model list, 60s timeout.
- Only temporary errors are retried (429, 5xx, timeouts); 401/400 are not, since retrying can't fix them.
- Added own Google AI Studio key via OpenRouter BYOK to avoid the crowded shared pool.
- Test result: first call got 503, retry succeeded → retry logic needed even with BYOK.