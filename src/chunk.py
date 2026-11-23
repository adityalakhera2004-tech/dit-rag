import json
from pathlib import Path
from statistics import median

from transformers import AutoTokenizer

PAGES_FILE = Path("data/processed/pages.jsonl")
OUT_FILE = Path("data/processed/chunks.jsonl")

MIN_TOKENS = 50     # merge pages until a chunk has at least this many tokens
MAX_TOKENS = 400    # never let a chunk grow past this (model limit is 512)

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")


def count_tokens(text):
    return len(tokenizer.encode(text, add_special_tokens=False))


def make_chunk(pages):
    """Combine one or more pages (same file) into a single chunk record."""
    first, last = pages[0], pages[-1]
    text = "\n\n".join(p["text"] for p in pages)
    return {
        "chunk_id": f"{first['course_code']}_{first['doc_type']}_p{first['page']}-{last['page']}",
        "source": first["source"],
        "course_code": first["course_code"],
        "doc_type": first["doc_type"],
        "page_start": first["page"],
        "page_end": last["page"],
        "pages": [p["page"] for p in pages],
        "n_tokens": count_tokens(text),
        "text": text,
    }


def chunk_pages(pages):
    chunks = []
    buffer, buffer_tokens = [], 0          # pages waiting to become a chunk

    for page in pages:
        n = count_tokens(page["text"])

        # Rule: never mix two files in one chunk
        if buffer and page["source"] != buffer[0]["source"]:
            chunks.append(make_chunk(buffer))
            buffer, buffer_tokens = [], 0

        # Rule: never go over MAX_TOKENS
        if buffer and buffer_tokens + n > MAX_TOKENS:
            chunks.append(make_chunk(buffer))
            buffer, buffer_tokens = [], 0

        buffer.append(page)
        buffer_tokens += n

        # Big enough? Then this chunk is finished
        if buffer_tokens >= MIN_TOKENS:
            chunks.append(make_chunk(buffer))
            buffer, buffer_tokens = [], 0

    if buffer:                              # leftover pages at the very end
        chunks.append(make_chunk(buffer))
    return chunks


def main():
    pages = [json.loads(line) for line in PAGES_FILE.open(encoding="utf-8")]
    chunks = chunk_pages(pages)

    with OUT_FILE.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    sizes = [c["n_tokens"] for c in chunks]
    merged = [c for c in chunks if c["page_end"] > c["page_start"]]
    print(f"{len(pages)} pages → {len(chunks)} chunks")
    print(f"Chunks covering more than one page: {len(merged)}")
    print(f"Tokens per chunk  min: {min(sizes)}  median: {median(sizes)}  max: {max(sizes)}")
    print(f"Chunks still under {MIN_TOKENS} tokens: {sum(s < MIN_TOKENS for s in sizes)}")
    print(f"Saved to {OUT_FILE}")


if __name__ == "__main__":
    main()