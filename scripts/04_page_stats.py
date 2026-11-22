import pymupdf

PDF_PATH = "data/raw/CSN441_notes_unit1.pdf"

doc = pymupdf.open(PDF_PATH)

empty_pages = []
for i, page in enumerate(doc):
    text = page.get_text().strip()
    page_number = i + 1            # humans count from 1, code counts from 0
    print(f"Page {page_number:>2}: {len(text):>5} characters")
    if len(text) < 20:
        empty_pages.append(page_number)

print("=" * 40)
print("Total pages:", len(doc))
print("Pages with almost no text:", empty_pages)

doc.close()