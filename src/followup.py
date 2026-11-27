import re

# Short questions containing these words usually refer back to the last answer
FOLLOW_UP_WORDS = {"it", "its", "this", "that", "these", "those", "they", "them",
                   "their", "more", "example", "examples", "again", "elaborate", "further"}

# Questions starting like this are almost always follow-ups
FOLLOW_UP_STARTS = ("and ", "also ", "what about", "how about", "tell me more",
                    "explain more", "explain it", "explain that", "explain this",
                    "give an example", "give me an example", "can you elaborate", "elaborate")


def is_follow_up(question):
    """Guess whether a question depends on the previous turn (rule-based, no LLM)."""
    q = question.lower().strip()
    q = q.replace("this course", "")          # "for this course" is not a follow-up
    words = re.findall(r"[a-z]+", q)
    if not words:
        return False
    if q.startswith(FOLLOW_UP_STARTS):
        return True
    return len(words) <= 8 and any(w in FOLLOW_UP_WORDS for w in words)