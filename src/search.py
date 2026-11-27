import argparse

from sentence_transformers import SentenceTransformer

from db import get_connection

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CANDIDATES = 20   # how many results each method contributes before merging
RRF_K = 60        # standard Reciprocal Rank Fusion constant
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Settings used by the app (chosen from the Day 11 evaluation)
USE_QUERY_PREFIX = False
KEYWORD_WEIGHT = 1.0
# Match ANY of the question's words (OR), not ALL of them (AND)
KEYWORD_QUERY = "to_tsquery('english', replace(plainto_tsquery('english', %s)::text, ' & ', ' | '))"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def vector_search(conn, question, course_code=None, limit=CANDIDATES, use_prefix=False):
    text = QUERY_PREFIX + question if use_prefix else question
    q_vec = get_model().encode(text, normalize_embeddings=True)
    where, params = ("WHERE course_code = %s", [course_code]) if course_code else ("", [])
    sql = f"""
        SELECT chunk_id, source, pages, text, 1 - (embedding <=> %s) AS score
        FROM chunks {where}
        ORDER BY embedding <=> %s
        LIMIT %s
    """
    return conn.execute(sql, [q_vec, *params, q_vec, limit]).fetchall()


def keyword_search(conn, question, course_code=None, limit=CANDIDATES):
    extra, params = ("AND course_code = %s", [course_code]) if course_code else ("", [])
    sql = f"""
        SELECT chunk_id, source, pages, text, ts_rank(text_search, query) AS score
        FROM chunks, {KEYWORD_QUERY} AS query
        WHERE text_search @@ query {extra}
        ORDER BY score DESC
        LIMIT %s
    """
    return conn.execute(sql, [question, *params, limit]).fetchall()


def rrf_merge(result_lists, k=RRF_K, weights=None):
    """Reciprocal Rank Fusion: each list gives a chunk weight / (k + rank) points."""
    weights = weights or [1.0] * len(result_lists)
    points, rows = {}, {}
    for results, weight in zip(result_lists, weights):
        for rank, row in enumerate(results, start=1):
            chunk_id = row[0]
            points[chunk_id] = points.get(chunk_id, 0) + weight / (k + rank)
            rows.setdefault(chunk_id, row)
    ranked = sorted(points, key=points.get, reverse=True)
    return [(*rows[c][:4], points[c]) for c in ranked]


def search(question, course_code=None, k=5, mode="hybrid"):
    with get_connection() as conn:
        if mode == "vector":
            return vector_search(conn, question, course_code, k, use_prefix=USE_QUERY_PREFIX)
        if mode == "keyword":
            return keyword_search(conn, question, course_code, k)
        merged = rrf_merge([vector_search(conn, question, course_code, use_prefix=USE_QUERY_PREFIX),
                            keyword_search(conn, question, course_code)],
                           weights=[1.0, KEYWORD_WEIGHT])
        return merged[:k]


def search_with_confidence(question, course_code=None, k=5):
    """Hybrid results PLUS the best vector similarity (how close the closest chunk is)."""
    with get_connection() as conn:
        vec = vector_search(conn, question, course_code, use_prefix=USE_QUERY_PREFIX)
        kw = keyword_search(conn, question, course_code)
    top_similarity = float(vec[0][4]) if vec else 0.0
    return rrf_merge([vec, kw], weights=[1.0, KEYWORD_WEIGHT])[:k], top_similarity


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search the course chunks.")
    parser.add_argument("question")
    parser.add_argument("--course", help="course code filter, e.g. CSN441")
    parser.add_argument("--mode", default="hybrid", choices=["vector", "keyword", "hybrid"])
    args = parser.parse_args()

    print(f"Q: {args.question}  [mode: {args.mode}, course: {args.course or 'all'}]")
    for chunk_id, source, pages, text, score in search(args.question, args.course, mode=args.mode):
        print(f"\n{score:.4f} | {source} | pages {pages}")
        print("   ", text[:120].replace("\n", " "))