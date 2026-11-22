import pymupdf

PDF_PATH = "data/raw/CSN441_notes_unit1.pdf"  # ← change to one of YOUR file names

doc = pymupdf.open(PDF_PATH)

print("File:", PDF_PATH)
print("Number of pages:", len(doc))
print("=" * 60)

first_page = doc[0]                  # pages are counted from 0 in code
text = first_page.get_text()         # pull all text from this page

print("Characters on page 1:", len(text))
print("=" * 60)
print(text[:1000])                   # show the first 1000 characters only

doc.close()