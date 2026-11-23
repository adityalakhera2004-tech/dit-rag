import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from db import get_connection

CHUNKS_FILE = Path("data/processed/chunks.jsonl")
MODEL_NAME = "BAAI/bge-small-en-v1.5"

INSERT_SQL = """
    INSERT INTO chunks
        (chunk_id, source, course_code, doc_type, page_start, page_end,
         pages, n_tokens, text, embedding)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def main():
    chunks = [json.loads(line) for line in CHUNKS_FILE.open(encoding="utf-8")]
    print(f"Loaded {len(chunks)} chunks")

    model = SentenceTransformer(MODEL_NAME)
    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts, normalize_embeddings=True,
                           batch_size=32, show_progress_bar=True)

    rows = [
        (c["chunk_id"], c["source"], c["course_code"], c["doc_type"],
         c["page_start"], c["page_end"], c["pages"], c["n_tokens"],
         c["text"], vec)
        for c, vec in zip(chunks, vectors)
    ]

    with get_connection() as conn:
        conn.execute("TRUNCATE chunks")          # remove old rows: full rebuild
        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)
        count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    print(f"Stored {count} chunks in the database")


if __name__ == "__main__":
    main()