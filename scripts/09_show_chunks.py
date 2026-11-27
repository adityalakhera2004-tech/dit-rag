import json
import sys
from pathlib import Path

course = sys.argv[1].upper() if len(sys.argv) > 1 else "CSN401"
chunks = [json.loads(line) for line in Path("data/processed/chunks.jsonl").open(encoding="utf-8")]

for c in chunks:
    if c["course_code"] == course and c["n_tokens"] >= 40:      # skip near-empty chunks
        preview = c["text"][:200].replace("\n", " ")
        print(f"\n{c['source']} | pages {c['pages']}\n   {preview}")