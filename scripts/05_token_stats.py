import json
from pathlib import Path
from statistics import mean, median

from sentence_transformers import SentenceTransformer

PAGES_FILE = Path("data/processed/pages.jsonl")

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
tokenizer = model.tokenizer
LIMIT = model.max_seq_length
print("Model's max tokens per chunk:", LIMIT)

# Read every page record back from the file we saved on Day 2
records = [json.loads(line) for line in PAGES_FILE.open(encoding="utf-8")]

counts = []
for r in records:
    n_tokens = len(tokenizer.encode(r["text"], add_special_tokens=False))
    counts.append((n_tokens, r["source"], r["page"]))

counts.sort()                                    # smallest first
tokens = [c[0] for c in counts]

print(f"Pages: {len(tokens)}")
print(f"Tokens per page  min: {min(tokens)}  median: {median(tokens)}  "
      f"average: {mean(tokens):.0f}  max: {max(tokens)}")
print(f"Pages over the {LIMIT}-token limit: {sum(t > LIMIT for t in tokens)}")
print(f"Pages under 50 tokens (very short): {sum(t < 50 for t in tokens)}")

print("\n5 smallest pages:")
for n, source, page in counts[:5]:
    print(f"  {n:>4} tokens | {source} page {page}")

print("\n5 largest pages:")
for n, source, page in counts[-5:]:
    print(f"  {n:>4} tokens | {source} page {page}")