import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, "src")                     # import our project code
from courses import detect_course
from db import get_connection
from rag import MIN_SIMILARITY, TOP_K, remove_duplicates
from search import keyword_search, rrf_merge, vector_search

QUESTIONS = Path("eval/questions.yaml")
OUT = Path("eval/results_retrieval.json")

# name: (use bge prefix?, hybrid?, keyword weight in RRF)
CONFIGS = {
    "vector":           (False, False, 0.0),
    "vector+prefix":    (True,  False, 0.0),
    "hybrid":           (False, True,  1.0),
    "hybrid+prefix":    (True,  True,  1.0),
    "hybrid+prefix+kw0.5": (True, True, 0.5),
}


def is_hit(row, q):
    """A result row is correct if it comes from the right file AND covers a right page."""
    sources = q["source"] if isinstance(q["source"], list) else [q["source"]]
    return row[1] in sources and bool(set(row[2]) & set(q["pages"]))


def first_hit_rank(results, q):
    """Rank (1-5) of the first correct chunk, or None if it's not in the list."""
    for rank, row in enumerate(results, start=1):
        if is_hit(row, q):
            return rank
    return None


def top_results(vec, kw, hybrid, kw_weight):
    merged = rrf_merge([vec, kw], weights=[1.0, kw_weight]) if hybrid else vec
    return remove_duplicates(merged)[:TOP_K]


def summarise(in_rows, name):
    ranks = [d["ranks"][name] for d in in_rows]
    n = len(ranks)
    return {"hit@1": sum(r == 1 for r in ranks) / n,
            "hit@5": sum(r is not None for r in ranks) / n,
            "mrr": sum(1 / r for r in ranks if r) / n}


def threshold_report(in_rows, out_rows, key, label):
    blocked = [d["id"] for d in in_rows if d[key] < MIN_SIMILARITY]
    caught = [d["id"] for d in out_rows if d[key] < MIN_SIMILARITY]
    print(f"\nTHRESHOLD {MIN_SIMILARITY} ({label})")
    print(f"  in-scope wrongly blocked:  {len(blocked)}/{len(in_rows)} {blocked}")
    print(f"  out-of-scope caught early: {len(caught)}/{len(out_rows)} {caught}")
    print(f"  lowest in-scope: {min(d[key] for d in in_rows):.3f} | "
          f"highest out-of-scope: {max(d[key] for d in out_rows):.3f}")


def main():
    questions = yaml.safe_load(QUESTIONS.open(encoding="utf-8"))
    details = []

    with get_connection() as conn:
        for q in questions:
            in_scope = q.get("type") != "out_of_scope"
            course, search_q, _ = detect_course(q["question"])     # same parsing as the bot
            vec_plain = vector_search(conn, search_q, course)
            vec_prefix = vector_search(conn, search_q, course, use_prefix=True)
            kw = keyword_search(conn, search_q, course)

            row = {"id": q["id"], "question": q["question"], "in_scope": in_scope,
                   "sim_plain": round(float(vec_plain[0][4]), 3) if vec_plain else 0.0,
                   "sim_prefix": round(float(vec_prefix[0][4]), 3) if vec_prefix else 0.0}
            if in_scope:
                row["ranks"] = {}
                for name, (prefix, hybrid, kw_weight) in CONFIGS.items():
                    vec = vec_prefix if prefix else vec_plain
                    row["ranks"][name] = first_hit_rank(top_results(vec, kw, hybrid, kw_weight), q)
            details.append(row)

    in_rows = [d for d in details if d["in_scope"]]
    out_rows = [d for d in details if not d["in_scope"]]
    summary = {name: summarise(in_rows, name) for name in CONFIGS}

    print(f"\nRETRIEVAL on {len(in_rows)} in-scope questions (top {TOP_K})")
    print(f"{'Config':<22} {'Hit@1':>7} {'Hit@5':>7} {'MRR':>6}")
    for name, s in summary.items():
        print(f"{name:<22} {s['hit@1']:>7.1%} {s['hit@5']:>7.1%} {s['mrr']:>6.3f}")

    print("\nPer question (rank of the correct chunk; - = not in top 5)")
    short = ["V", "V+P", "H", "H+P", "H+P.5"]
    print(f"{'id':<5} " + " ".join(f"{s:>5}" for s in short) + "  question")
    for d in in_rows:
        cells = " ".join(f"{(d['ranks'][n] or '-'):>5}" for n in CONFIGS)
        print(f"{d['id']:<5} {cells}  {d['question']}")

    threshold_report(in_rows, out_rows, "sim_plain", "without prefix")
    threshold_report(in_rows, out_rows, "sim_prefix", "with prefix")

    OUT.write_text(json.dumps({"summary": summary, "details": details}, indent=2))
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()