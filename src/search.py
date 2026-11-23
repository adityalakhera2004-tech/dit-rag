import sys

from sentence_transformers import SentenceTransformer

from db import get_connection

MODEL_NAME = "BAAI/bge-small-en-v1.5"
_model = None


def get_model():
    global _model
    if _model is None:                # load the model only once
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def search(question, course_code=None, k=5):
    q_vec = get_model().encode(question, normalize_embeddings=True)

    sql = """
        SELECT chunk_id, source, pages, text,
               1 - (embedding <=> %s) AS score
        FROM chunks
    """
    params = [q_vec]
    if course_code:
        sql += " WHERE course_code = %s"
        params.append(course_code)
    sql += " ORDER BY embedding <=> %s LIMIT %s"
    params += [q_vec, k]

    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "What is a translator?"
    course = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Q: {question}" + (f"  [course: {course}]" if course else ""))
    for chunk_id, source, pages, text, score in search(question, course):
        print(f"\n{score:.3f} | {source} | pages {pages}")
        print("   ", text[:150].replace("\n", " "))