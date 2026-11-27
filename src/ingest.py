import json
import re
from pathlib import Path

import pymupdf

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/processed/pages.jsonl")
MIN_CHARS = 20   # pages with less text than this are skipped (title/"Thank you" slides)

# 3+ capital letters each separated by ONE space, e.g. "P H A S E" (words are separated by 2+ spaces)
LETTER_SPACED = re.compile(r"\b[A-Z](?: [A-Z]){2,}\b")


def parse_filename(pdf_path):
    """CSN441_notes_unit1.pdf  ->  ("CSN441", "notes_unit1")"""
    parts = pdf_path.stem.split("_", 1)
    course_code = parts[0].upper()
    doc_type = parts[1].lower() if len(parts) > 1 else "unknown"
    if not re.fullmatch(r"[A-Z]{3}\d{3}", course_code):
        print(f"  WARNING: '{course_code}' doesn't look like a course code (e.g. CSN441)")
    return course_code, doc_type


def clean_text(text):
    text = text.replace("\u00a0", " ")             # odd invisible spaces → normal spaces
    # Day 11: join letter-spaced headings BEFORE collapsing spaces: "P H A S E" → "PHASE"
    text = LETTER_SPACED.sub(lambda m: m.group(0).replace(" ", ""), text)
    text = re.sub(r"[ \t]+", " ", text)            # many spaces → one space
    text = re.sub(r"\n{3,}", "\n\n", text)         # many blank lines → one blank line
    return text.strip()


def extract_pdf(pdf_path):
    course_code, doc_type = parse_filename(pdf_path)
    records, skipped = [], []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            text = clean_text(page.get_text())
            page_number = i + 1
            if len(text) < MIN_CHARS:
                skipped.append(page_number)
                continue
            records.append({
                "source": pdf_path.name,
                "course_code": course_code,
                "doc_type": doc_type,
                "page": page_number,
                "text": text,
            })
    return records, skipped


def main():
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in", RAW_DIR)
        return

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for pdf_path in pdf_files:
            print(f"Reading {pdf_path.name}")
            records, skipped = extract_pdf(pdf_path)
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            total += len(records)
            print(f"  kept {len(records)} pages, skipped {skipped}")

    print(f"\nDone: {total} pages from {len(pdf_files)} PDFs → {OUT_FILE}")


if __name__ == "__main__":
    main()