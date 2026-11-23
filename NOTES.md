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


## DAY 2 : 
- Extracted 193 pages from 3 PDFs (CSN401: 55, CSN441: 32, CSN442: 106).
- CSN442: 43/149 pages (29%) image-only, incl. pages 62-82 → no text. Known limitation; OCR only if eval shows missing answers.
- doc_type lower-cased so "Unit1" and "unit1" match (normalisation).
- Text issues seen: letter-spaced headings ("R O A D M A P"), repeated footer per slide, diagram labels as loose words.
- Slide counter "03 / 55" appears on PDF page 2 → citations use PDF page number (what users navigate by), not the slide label.
- Footer "CSN401 · Compiler Design · Unit 1" kept: it adds the course name to every chunk.

## Day 3: Chunking
- Token stats (bge tokenizer): 243 pages, median 103, max 360, 0 over the 512 limit, 52 under 50 tokens.
- Rule: 1 slide = 1 chunk; merge slides under 50 tokens with the next; never mix files; max 400 tokens.
- Result: 243 pages → 196 chunks, 40 multi-page, median 128.5 tokens, 1 under 50 (final "Thank you" slide).
- Found: chunk "p125-130" really held pages 125, 129, 130 (126-128 image-only) → chunks now store an exact "pages" list.
- Open question for Day 11: should merging stop at page gaps?