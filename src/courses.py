import re

# The courses we have material for: code → course name
COURSES = {
    "CSN401": "Compiler Design",
    "CSN441": "Fuzzy Logic & Neural Network",
    "CSN442": "Evolutionary Computing",
}

CODE_PATTERN = re.compile(r"\b([A-Za-z]{3})\s*-?\s*(\d{3})\b")


def tidy(text):
    text = re.sub(r"\s+", " ", text)              # many spaces → one
    text = re.sub(r"\s+([?.!,])", r"\1", text)     # "course ?" → "course?"
    return text.strip()


def detect_course(question):
    """
    Returns (course_code, search_question, unknown_code).
    - course_code:     e.g. "CSN441" if found and known, else None
    - search_question: the question with the code replaced by "this course"
    - unknown_code:    e.g. "CSN999" if a code was typed but we have no material
    """
    match = CODE_PATTERN.search(question)
    if match:
        code = (match.group(1) + match.group(2)).upper()
        if code in COURSES:
            # Replace (not delete) the code: deleting left broken questions like
            # "prerequisites for?", which dropped the right slide out of the top 5.
            cleaned = question[:match.start()] + "this course" + question[match.end():]
            return code, tidy(cleaned), None
        return None, question, code

    lowered = question.lower()
    for code, name in COURSES.items():
        if name.lower() in lowered:
            return code, question, None

    return None, question, None