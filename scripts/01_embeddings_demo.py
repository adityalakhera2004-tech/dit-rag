from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

chunks = [
    "Evaluation: Mid-semester exam 25%, End-semester exam 50%, Quizzes 15%, Assignments 10%.",
    "Unit 3 covers process scheduling: FCFS, SJF, Round Robin.",
    "The computer lab is located in Block C, second floor.",
    "Attendance below 75% will result in debarment from the end-semester exam.",
]
chunk_vecs = model.encode(chunks, normalize_embeddings=True)

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
questions = [
    "How are marks divided in CSN 401?",   # with course code
    "How are marks divided?",              # without course code
]

for question in questions:
    for use_prefix in [False, True]:
        text = QUERY_PREFIX + question if use_prefix else question
        q_vec = model.encode(text, normalize_embeddings=True)
        scores = util.cos_sim(q_vec, chunk_vecs)[0]
        ranked = sorted(zip(chunks, scores), key=lambda x: -x[1])

        print(f"\nQ: {question!r} | prefix={use_prefix}")
        for chunk, score in ranked[:2]:          # show top 2 only
            print(f"  {score:.3f} | {chunk[:50]}")