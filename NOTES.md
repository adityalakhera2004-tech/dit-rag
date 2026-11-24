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

## Day 4: Embeddings + pgvector
- Postgres 17 + pgvector in Docker (port 5433, volume ditrag_pgdata). Table: chunks with vector(384), index on course_code.
- embed_store.py: full rebuild (TRUNCATE + INSERT in one transaction), bge-small, normalized, batch 32.
- search.py: cosine distance (<=>), top-k = 5, optional WHERE course_code filter, %s placeholders (no SQL injection).
- "What is a translator?" → correct chunk (p3-4) at 0.840, next 0.657 → clear winner.
- "What is a perceptron?" → correct at 0.760, but chunk [39, 42] merged a "Hebbian Learning" title with the Perceptron slide across a gap → real example for the Day 11 gap question.
- Equations extract as garbage characters (e.g. CSN441 unit3 p22-23) → known limitation for formula questions.
- "Prerequisites for this course?" no filter → CSN441 p1 first, but 3/5 results from other courses. With CSN441 filter → 5/5 from CSN441. UI needs a course selector.
- Same course-info slide in CSN441 unit1 + unit3 → duplicate chunks fill 2/5 places → add deduplication.
- Keyword-style questions ("prerequisites") score lower (0.626) → motivation for hybrid search (Day 7).

## Day 6: Course detection
- courses.py: regex \b([A-Za-z]{3})\s*-?\s*(\d{3})\b detects CSN441 / CSN 441 / csn-441; course names map to codes.
- Unknown code (CSN999) → instant reply with available courses, no search, no LLM call.
- Regression: deleting the code ("prerequisites for?") dropped the right slide out of the top 5.
  Tested retrieval alone: delete = not in top 5, "this course" = #1, course name = #5 (Textbooks slide won).
  Fix: replace the code with "this course".
- pytest: 7 tests for detect_course, all passing.