import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

load_dotenv()

EMBED_DIM = 384   # bge-small turns every text into 384 numbers


def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL not found. Check your .env file.")
    conn = psycopg.connect(url)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)          # lets Python send/receive vectors
    return conn


SCHEMA = [
    f"""
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id     TEXT PRIMARY KEY,
        source       TEXT NOT NULL,
        course_code  TEXT NOT NULL,
        doc_type     TEXT NOT NULL,
        page_start   INT  NOT NULL,
        page_end     INT  NOT NULL,
        pages        INT[] NOT NULL,
        n_tokens     INT,
        text         TEXT NOT NULL,
        embedding    vector({EMBED_DIM}) NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_chunks_course ON chunks (course_code)",
    # Day 7: keyword search. Postgres fills this column automatically from `text`.
    """
    ALTER TABLE chunks ADD COLUMN IF NOT EXISTS text_search tsvector
        GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
    """,
    "CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks USING GIN (text_search)",
]


def create_tables():
    with get_connection() as conn:
        for statement in SCHEMA:
            conn.execute(statement)
    print("Table 'chunks' is ready.")


if __name__ == "__main__":
    create_tables()