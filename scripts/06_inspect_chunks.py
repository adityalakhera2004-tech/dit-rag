import json
from pathlib import Path

chunks = [json.loads(line) for line in Path("data/processed/chunks.jsonl").open(encoding="utf-8")]


def show(title, c):
    print(f"\n=== {title}: {c['chunk_id']} ({c['n_tokens']} tokens) | pages {c.get('pages')} ===")
    print(c["text"][:500])


smallest = min(chunks, key=lambda c: c["n_tokens"])
show("Smallest chunk", smallest)

merged = [c for c in chunks if c["page_end"] > c["page_start"]]
show("A merged chunk", merged[0])

widest = max(chunks, key=lambda c: c["page_end"] - c["page_start"])
span = widest["page_end"] - widest["page_start"] + 1
show(f"Chunk covering the most pages ({span} pages)", widest)