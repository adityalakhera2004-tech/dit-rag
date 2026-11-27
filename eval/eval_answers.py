import json
import re
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, "src")
from rag import answer

QUESTIONS = Path("eval/questions.yaml")
ANSWERS = Path("eval/answers.jsonl")      # one line per question, saved as we go
OUT = Path("eval/results_answers.json")
PAUSE_SECONDS = 6                         # stay under the free tier's per-minute limit


def load_done():
    """Answers saved by earlier runs, so nothing is asked twice."""
    if not ANSWERS.exists():
        return {}
    return {r["id"]: r for r in map(json.loads, ANSWERS.open(encoding="utf-8"))}


def parse_label(label):
    """'CSN441_notes_unit3.pdf, pages 39, 42' -> ('CSN441_notes_unit3.pdf', [39, 42])"""
    source, _, page_part = label.partition(", page")
    pages = set()
    for a, b in re.findall(r"(\d+)(?:-(\d+))?", page_part):
        pages.update(range(int(a), int(b or a) + 1))
    return source, sorted(pages)


def run_question(q):
    result = answer(q["question"])
    cited = [parse_label(s["label"]) for s in result["sources"] if s["n"] in result["cited"]]
    return {"id": q["id"], "question": q["question"], "answer": result["answer"],
            "model": result["model"], "refused": result["refused"],
            "top_similarity": result["top_similarity"], "cited": cited,
            "invalid_citations": result["invalid_citations"]}


def is_refusal(rec):
    return rec["refused"] is not None or "couldn't find" in rec["answer"].lower()


def contains_all(text, words):
    text = text.lower()
    return all(w.lower() in text for w in words)


def cites_correct_page(rec, q):
    sources = q["source"] if isinstance(q["source"], list) else [q["source"]]
    return any(src in sources and set(pages) & set(q["pages"]) for src, pages in rec["cited"])


def score(questions, done):
    in_q = [q for q in questions if q.get("type") != "out_of_scope" and q["id"] in done]
    out_q = [q for q in questions if q.get("type") == "out_of_scope" and q["id"] in done]

    answered, facts_ok, cite_ok, fails = 0, 0, 0, []
    for q in in_q:
        rec = done[q["id"]]
        if is_refusal(rec):
            fails.append((q["id"], "refused a real question"))
            continue
        answered += 1
        ok_facts = contains_all(rec["answer"], q["must_include"])
        ok_cite = cites_correct_page(rec, q)
        facts_ok += ok_facts
        cite_ok += ok_cite
        if not ok_facts:
            fails.append((q["id"], f"missing {q['must_include']}"))
        if not ok_cite:
            fails.append((q["id"], "didn't cite the correct page"))

    refused = [q["id"] for q in out_q if is_refusal(done[q["id"]])]
    early = [q["id"] for q in out_q if done[q["id"]]["refused"] is not None]
    invalid = sum(len(done[q["id"]]["invalid_citations"]) for q in in_q)
    models = sorted({done[q["id"]]["model"] for q in in_q + out_q if done[q["id"]]["model"]})

    n_in, n_out = len(in_q), len(out_q)
    print(f"\nANSWERS: {n_in} in-scope, {n_out} out-of-scope evaluated")
    print(f"  Answered (not refused):        {answered}/{n_in}")
    print(f"  Contains key facts:            {facts_ok}/{n_in}")
    print(f"  Cites the correct page:        {cite_ok}/{n_in}")
    print(f"  Invalid (made-up) citations:   {invalid}")
    print(f"  Out-of-scope refused:          {len(refused)}/{n_out}  (early, no LLM: {len(early)})")
    not_refused = [q["id"] for q in out_q if q["id"] not in refused]
    if not_refused:
        print(f"  ⚠️ Out-of-scope ANSWERED: {not_refused}")
    print(f"  Models used: {models}")
    if fails:
        print("\nTo review by hand:")
        for qid, reason in fails:
            print(f"  {qid}: {reason}")

    summary = {"in_scope": n_in, "answered": answered, "facts_ok": facts_ok, "cite_ok": cite_ok,
               "invalid_citations": invalid, "out_of_scope": n_out, "refused": len(refused),
               "refused_early": len(early), "models": models, "fails": fails}
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"\nSaved summary to {OUT} (all answers in {ANSWERS})")


def main():
    questions = yaml.safe_load(QUESTIONS.open(encoding="utf-8"))
    done = load_done()
    todo = [q for q in questions if q["id"] not in done]
    print(f"{len(done)} already answered, {len(todo)} to go")

    with ANSWERS.open("a", encoding="utf-8") as f:
        for i, q in enumerate(todo, start=1):
            try:
                rec = run_question(q)
            except RuntimeError:
                print("\nAll models are busy. Progress is saved; run this script again later to continue.")
                break
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()                                   # write to disk now, not later
            done[q["id"]] = rec
            print(f"[{i}/{len(todo)}] {q['id']}: {'refused (' + rec['refused'] + ')' if rec['refused'] else rec['model']}")
            if rec["model"]:
                time.sleep(PAUSE_SECONDS)

    score(questions, done)


if __name__ == "__main__":
    main()